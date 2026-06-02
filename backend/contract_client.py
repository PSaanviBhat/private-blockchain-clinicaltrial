"""
Web3 bridge for mirroring selected backend actions to the local Hardhat contract.
"""
from __future__ import annotations

import json
from dataclasses import is_dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from web3 import Web3


class ContractMirrorService:
    ROLE_MAP = {
        "PROTOCOL_VALIDATOR": 1,
        "CONSENT_VERIFIER": 2,
        "COMPLIANCE_AUDITOR": 3,
    }

    def __init__(self, rpc_url: str, deployment_path: str, contract_name: str = "ClinicalTrialRegistry"):
        self.rpc_url = rpc_url
        self.deployment_path = Path(deployment_path)
        self.contract_name = contract_name
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 30}))
        self.contract = None
        self.contract_address = ""
        self.abi: list[dict] = []
        self.deployer = ""
        self.enabled = False
        self.reload()

    @classmethod
    def from_settings(cls, settings) -> "ContractMirrorService":
        return cls(settings.hardhat_rpc_url, settings.contract_deployment_path, settings.contract_name)

    def reload(self) -> bool:
        data: Dict[str, Any] = {}
        if self.deployment_path.exists():
            try:
                data = json.loads(self.deployment_path.read_text(encoding="utf-8"))
            except Exception:
                data = {}

        address = data.get("address") or data.get("contract_address") or ""
        abi = data.get("abi") or []
        if not address or not abi or not self.web3.is_connected():
            self.enabled = False
            self.contract = None
            return False

        self.contract_address = Web3.to_checksum_address(address)
        self.abi = abi
        self.deployer = data.get("deployer") or data.get("deployer_account") or ""
        self.contract = self.web3.eth.contract(address=self.contract_address, abi=self.abi)
        self.enabled = True
        return True

    def health(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "connected": self.web3.is_connected(),
            "rpc_url": self.rpc_url,
            "deployment_path": str(self.deployment_path),
            "contract_address": self.contract_address,
            "deployer": self.deployer,
        }

    @staticmethod
    def _node_value(node: Any, key: str, default: Any = None) -> Any:
        if isinstance(node, dict):
            return node.get(key, default)
        return getattr(node, key, default)

    def _get_node_account(self, node: Any):
        private_key = self._node_value(node, "private_key")
        if not private_key:
            return None
        try:
            return self.web3.eth.account.from_key(private_key)
        except Exception:
            return None

    def _tx_params(self, from_address: str) -> Dict[str, Any]:
        return {
            "from": Web3.to_checksum_address(from_address),
            "nonce": self.web3.eth.get_transaction_count(Web3.to_checksum_address(from_address)),
            "gas": 2_500_000,
            "gasPrice": self.web3.eth.gas_price,
        }

    def _send_contract_call(self, fn, from_address: str, private_key: Optional[str] = None) -> Dict[str, Any]:
        if private_key:
            tx = fn.build_transaction(self._tx_params(from_address))
            signed = self.web3.eth.account.sign_transaction(tx, private_key=private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
        else:
            tx_hash = fn.transact(self._tx_params(from_address))
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        return {
            "ok": receipt.status == 1,
            "tx_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "contract_address": self.contract_address,
        }

    def _ensure_ready(self) -> bool:
        if self.enabled and self.contract is not None:
            return True
        return self.reload()

    def bootstrap_nodes(self, registry) -> Dict[str, Any]:
        if not self._ensure_ready():
            return {"enabled": False, "mirrored": 0, "skipped": True}

        mirrored = 0
        errors: list[str] = []
        for node_summary in registry.list_nodes():
            node = registry.get(node_summary["node_id"])
            if node is None:
                continue
            result = self.mirror_register_node(node)
            if result.get("ok"):
                mirrored += 1
            else:
                errors.append(result.get("reason", "registration failed"))
        return {"enabled": True, "mirrored": mirrored, "errors": errors}

    def mirror_register_node(self, node: Any) -> Dict[str, Any]:
        if not self._ensure_ready():
            return {"ok": False, "reason": "contract bridge disabled"}

        account = self._get_node_account(node)
        if account is None:
            return {"ok": False, "reason": "node private key unavailable"}

        role = self._node_value(node, "role")
        role_name = getattr(role, "value", role)
        role_id = self.ROLE_MAP.get(str(role_name))
        if role_id is None:
            return {"ok": False, "reason": f"unsupported role: {role_name}"}

        contract_call = self.contract.functions.registerNode(
            account.address,
            role_id,
            self._node_value(node, "organization", "Unknown"),
        )
        try:
            return self._send_contract_call(contract_call, self.deployer)
        except Exception as exc:
            return {"ok": False, "reason": str(exc)}

    @staticmethod
    def _bytes32(value: str) -> bytes:
        hex_value = value[2:] if value.startswith("0x") else value
        return bytes.fromhex(hex_value)

    def mirror_submit_trial(self, transaction: Any) -> Dict[str, Any]:
        if not self._ensure_ready():
            return {"ok": False, "reason": "contract bridge disabled"}

        node = self._get_node_by_id(self._node_value(transaction, "node_id"))
        account = self._get_node_account(node)
        if account is None:
            return {"ok": False, "reason": "node account unavailable"}

        metadata = self._node_value(transaction, "metadata", {}) or {}
        dropout_rate = int(metadata.get("dropout_rate", metadata.get("dropoutRate", 0)) or 0)
        ml_approved = bool(metadata.get("ml_approved", metadata.get("mlApproved", True)))
        compliance_label = str(metadata.get("compliance_label", metadata.get("complianceLabel", "")))
        data_hash = str(self._node_value(transaction, "data_hash", ""))
        if not data_hash:
            return {"ok": False, "reason": "missing data hash"}

        contract_call = self.contract.functions.submitTrial(
            str(self._node_value(transaction, "trial_id")),
            self._bytes32(data_hash),
            str(self._node_value(transaction, "ipfs_cid", "")),
            dropout_rate,
            ml_approved,
            compliance_label,
        )
        try:
            return self._send_contract_call(contract_call, account.address, account.key.hex())
        except Exception as exc:
            return {"ok": False, "reason": str(exc)}

    def mirror_append_block(self, block: Any, validator_id: str) -> Dict[str, Any]:
        if not self._ensure_ready():
            return {"ok": False, "reason": "contract bridge disabled"}

        node = self._get_node_by_id(validator_id)
        account = self._get_node_account(node)
        if account is None:
            return {"ok": False, "reason": "validator account unavailable"}

        transactions = self._node_value(block, "transactions", []) or []
        transaction_ids = [str(tx.get("tx_id", tx)) if isinstance(tx, dict) else str(tx) for tx in transactions]
        merkle_root = str(self._node_value(block, "merkle_root", ""))
        if not merkle_root:
            return {"ok": False, "reason": "missing merkle root"}

        contract_call = self.contract.functions.appendBlock(
            self._bytes32(merkle_root),
            transaction_ids,
        )
        try:
            return self._send_contract_call(contract_call, account.address, account.key.hex())
        except Exception as exc:
            return {"ok": False, "reason": str(exc)}

    def mirror_audit_trial(self, trial_id: str, action: str, auditor_id: str) -> Dict[str, Any]:
        if not self._ensure_ready():
            return {"ok": False, "reason": "contract bridge disabled"}

        node = self._get_node_by_id(auditor_id)
        account = self._get_node_account(node)
        if account is None:
            return {"ok": False, "reason": "auditor account unavailable"}

        contract_call = self.contract.functions.auditTrial(str(trial_id), str(action))
        try:
            return self._send_contract_call(contract_call, account.address, account.key.hex())
        except Exception as exc:
            return {"ok": False, "reason": str(exc)}

    def _get_node_by_id(self, node_id: Optional[str]) -> Any:
        if not node_id:
            return None
        return self.registry.get(node_id) if hasattr(self, "registry") else None

    def attach_registry(self, registry) -> None:
        self.registry = registry
