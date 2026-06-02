"""
Step 10: IPFS Integration
- Upload encrypted clinical trial files to IPFS
- Return CID + original SHA-256 hash for on-chain storage
- On-chain/off-chain linking: timestamp + Trial ID + CID
"""
import base64
import hashlib, json, os, time, tempfile
from pathlib import Path
from typing import Dict, Optional

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    CRYPTO_AVAILABLE = True
except ImportError:
    AESGCM = None
    CRYPTO_AVAILABLE = False

try:
    import ipfshttpclient
    IPFS_AVAILABLE = True
except ImportError:
    IPFS_AVAILABLE = False


# ──────────────────────────────────────────────────────────────
# IPFS Client Wrapper
# ──────────────────────────────────────────────────────────────

class IPFSClient:
    """
    Wraps ipfshttpclient to upload / pin / retrieve content.
    Mock mode is explicit; real mode raises when the daemon is unavailable.
    """

    def __init__(self, api_url: str = "/ip4/127.0.0.1/tcp/5001", mode: str = "real"):
        self.api_url   = api_url
        self.mode      = (mode or "real").strip().lower()
        self._client   = None
        self._mock: Dict[str, bytes] = {}    # cid → content (mock)
        self._connected = False
        if self.mode not in {"real", "mock"}:
            raise ValueError("IPFS_MODE must be 'real' or 'mock'")
        self._try_connect()

    def _try_connect(self):
        if self.mode == "mock":
            print("IPFS: mock mode enabled")
            return
        if not IPFS_AVAILABLE:
            raise RuntimeError("IPFS_MODE=real requires ipfshttpclient to be installed")
        try:
            self._client = ipfshttpclient.connect(self.api_url)
            self._connected = True
            print(f"IPFS: connected to daemon at {self.api_url}")
        except Exception as e:
            raise RuntimeError(f"IPFS_MODE=real but daemon unavailable at {self.api_url}: {e}") from e

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.b64encode(value).decode("ascii")

    @staticmethod
    def _decode(value: str) -> bytes:
        return base64.b64decode(value.encode("ascii"))

    def encrypt_bytes(self, data: bytes) -> Dict:
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("AES encryption requires the cryptography package")

        key = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(12)
        cipher = AESGCM(key)
        ciphertext = cipher.encrypt(nonce, data, None)
        return {
            "ciphertext": ciphertext,
            "encryption_key_b64": self._encode(key),
            "nonce_b64": self._encode(nonce),
            "original_sha256": hashlib.sha256(data).hexdigest(),
            "ciphertext_sha256": hashlib.sha256(ciphertext).hexdigest(),
            "plaintext_size_bytes": len(data),
            "ciphertext_size_bytes": len(ciphertext),
        }

    # ── Upload ────────────────────────────────────────────────

    def upload_bytes(self, data: bytes, filename: str = "data.json") -> Dict:
        """Encrypt bytes, then upload to IPFS; return CID + hashes + local key."""
        encrypted = self.encrypt_bytes(data)
        payload = encrypted["ciphertext"]

        if self._connected and self._client:
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix,
                                             delete=False) as tmp:
                tmp.write(payload); tmp_path = tmp.name
            try:
                result = self._client.add(tmp_path, pin=True)
                cid    = result["Hash"]
            finally:
                os.unlink(tmp_path)
        elif self.mode == "mock":
            # Explicit demo-only mock CID derived from encrypted payload.
            cid = "Qm" + encrypted["ciphertext_sha256"][:44]
            self._mock[cid] = payload
        else:
            raise RuntimeError("IPFS_MODE=real requires a reachable IPFS daemon")

        return {
            "cid": cid,
            "original_sha256": encrypted["original_sha256"],
            "ciphertext_sha256": encrypted["ciphertext_sha256"],
            "encryption_key_b64": encrypted["encryption_key_b64"],
            "nonce_b64": encrypted["nonce_b64"],
            "plaintext_size_bytes": encrypted["plaintext_size_bytes"],
            "ciphertext_size_bytes": encrypted["ciphertext_size_bytes"],
            "mode": self.mode,
        }

    def upload_dict(self, record: dict) -> Dict:
        data = json.dumps(record, indent=2, default=str).encode("utf-8")
        return self.upload_bytes(data, "record.json")

    def upload_file(self, filepath: str) -> Dict:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        data = path.read_bytes()
        return self.upload_bytes(data, path.name)

    # ── Retrieve ──────────────────────────────────────────────

    def retrieve(self, cid: str) -> Optional[bytes]:
        if self._connected and self._client:
            try:
                return self._client.cat(cid)
            except Exception as e:
                print(f"IPFS retrieve error: {e}")
                return None
        return self._mock.get(cid)

    # ── On-chain link record ──────────────────────────────────

    def build_link_record(
        self,
        trial_id: str,
        cid: str,
        sha256: str,
        uploader_node_id: str,
    ) -> Dict:
        """
        Produces a minimal record to be stored on-chain:
        { trial_id, cid, sha256, timestamp, uploader }.
        This is what the smart contract stores (not the raw data).
        """
        return {
            "trial_id":         trial_id,
            "ipfs_cid":         cid,
            "sha256_hash":      sha256,
            "timestamp":        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "uploader_node_id": uploader_node_id,
        }

    def status(self) -> Dict:
        return {
            "mode":         self.mode,
            "connected":    self._connected,
            "api_url":      self.api_url,
            "mock_entries": len(self._mock),
            "ipfs_available": IPFS_AVAILABLE,
            "crypto_available": CRYPTO_AVAILABLE,
        }


# ──────────────────────────────────────────────────────────────
# On-chain vs Off-chain Comparison
# ──────────────────────────────────────────────────────────────

COMPARISON_TABLE = {
    "Feature":       ["On-Chain", "Off-Chain (IPFS)"],
    "Storage Cost":  ["Very High (~$$/KB on Ethereum)", "Very Low (free/peer-hosted)"],
    "Size Limit":    ["Tiny (<1 KB typical)", "No hard limit (GBs possible)"],
    "Immutability":  ["Absolute — cannot alter", "Content-addressed (CID locked)"],
    "Privacy":       ["Public (unless private chain)", "Public by default; can encrypt"],
    "Speed":         ["Slow (block time)", "Fast (direct content fetch)"],
    "Use Case":      ["Hashes, CIDs, metadata", "Raw data, genomic files, docs"],
}


def print_comparison():
    print("\n" + "="*70)
    print("On-Chain vs Off-Chain (IPFS) Storage Comparison")
    print("="*70)
    for feature, vals in COMPARISON_TABLE.items():
        print(f"\n{feature}:")
        print(f"  On-Chain  : {vals[0]}")
        print(f"  Off-Chain : {vals[1]}")
    print("="*70)


# ──────────────────────────────────────────────────────────────
# Self-test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    client = IPFSClient(mode="mock")

    sample = {
        "trial_id":    "NCT03000001",
        "patient_id":  "PAT-010001",
        "drug_name":   "Metformin",
        "genomic_ref": "BRCA1:c.5266dupC",
        "raw_logs":    "Dosage administered at 08:00. Patient stable. Adverse: Mild nausea.",
    }

    print("\n📤 Uploading to IPFS…")
    result = client.upload_dict(sample)
    print(f"  CID    : {result['cid']}")
    print(f"  SHA256 : {result['original_sha256']}")
    print(f"  Size   : {result['ciphertext_size_bytes']} bytes")

    link = client.build_link_record(
        "NCT03000001", result["cid"], result["original_sha256"], "NODE-01"
    )
    print("\n🔗 On-chain link record:")
    for k, v in link.items():
        print(f"  {k}: {v}")

    print("\n📥 Retrieve from IPFS:")
    content = client.retrieve(result["cid"])
    print(f"  Retrieved {len(content)} bytes" if content else "  Failed")

    print_comparison()
    print("\nStatus:", client.status())
