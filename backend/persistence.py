"""
SQLite-backed persistence for the local ledger prototype.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class SQLiteLedgerStore:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS blocks (
                    block_index INTEGER PRIMARY KEY,
                    block_hash TEXT NOT NULL UNIQUE,
                    previous_hash TEXT NOT NULL,
                    merkle_root TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    transactions_json TEXT NOT NULL,
                    validator_id TEXT NOT NULL,
                    validator_sig TEXT NOT NULL,
                    nonce INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS nodes (
                    node_id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    organization TEXT NOT NULL,
                    reputation_score REAL NOT NULL,
                    accuracy_score REAL NOT NULL,
                    private_key TEXT NOT NULL,
                    active INTEGER NOT NULL,
                    validated_count INTEGER NOT NULL,
                    rejected_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    tx_id TEXT PRIMARY KEY,
                    trial_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    data_hash TEXT NOT NULL,
                    ipfs_cid TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    signature TEXT,
                    status TEXT NOT NULL,
                    ml_result TEXT,
                    ml_confidence REAL
                );

                CREATE TABLE IF NOT EXISTS governance_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    pending_tx_count INTEGER NOT NULL,
                    avg_approval_ms REAL NOT NULL,
                    tps REAL NOT NULL,
                    model_accuracy REAL NOT NULL,
                    node_stats_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS governance_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    target_node TEXT,
                    delta REAL NOT NULL,
                    reason TEXT NOT NULL,
                    timestamp REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rejected_datasets (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_rows INTEGER NOT NULL,
                    flagged_rows INTEGER NOT NULL,
                    flagged_rate_pct REAL NOT NULL,
                    rows_json TEXT NOT NULL,
                    screening_json TEXT NOT NULL,
                    balance_report_json TEXT NOT NULL,
                    columns_json TEXT NOT NULL,
                    approved_by TEXT,
                    approved_at TEXT,
                    approval_note TEXT,
                    tx_ids_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ipfs_link_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trial_id TEXT NOT NULL,
                    ipfs_cid TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    uploader_node_id TEXT NOT NULL,
                    record_json TEXT NOT NULL
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _dump(value: Any) -> str:
        return json.dumps(value, default=str)

    @staticmethod
    def _load(value: Optional[str], default: Any) -> Any:
        if not value:
            return default
        return json.loads(value)

    def _execute(self, query: str, params: Iterable[Any] = ()) -> None:
        conn = self._connect()
        try:
            conn.execute(query, tuple(params))
            conn.commit()
        finally:
            conn.close()

    def _fetch_all(self, query: str, params: Iterable[Any] = ()) -> List[Dict]:
        conn = self._connect()
        try:
            rows = conn.execute(query, tuple(params)).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def load_blocks(self) -> List[Dict]:
        rows = self._fetch_all("SELECT * FROM blocks ORDER BY block_index ASC")
        for row in rows:
            row["index"] = row.pop("block_index")
            row["transactions"] = self._load(row.pop("transactions_json"), [])
        return rows

    def save_block(self, block: Dict) -> None:
        self._execute(
            """
            INSERT INTO blocks (
                block_index, block_hash, previous_hash, merkle_root, timestamp,
                transactions_json, validator_id, validator_sig, nonce
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(block_index) DO UPDATE SET
                block_hash=excluded.block_hash,
                previous_hash=excluded.previous_hash,
                merkle_root=excluded.merkle_root,
                timestamp=excluded.timestamp,
                transactions_json=excluded.transactions_json,
                validator_id=excluded.validator_id,
                validator_sig=excluded.validator_sig,
                nonce=excluded.nonce
            """,
            (
                block["index"],
                block["block_hash"],
                block["previous_hash"],
                block["merkle_root"],
                block["timestamp"],
                self._dump(block.get("transactions", [])),
                block["validator_id"],
                block["validator_sig"],
                block.get("nonce", 0),
            ),
        )

    def load_nodes(self) -> List[Dict]:
        return self._fetch_all("SELECT * FROM nodes ORDER BY node_id ASC")

    def save_node(self, node: Dict) -> None:
        role = getattr(node.get("role"), "value", node.get("role"))
        self._execute(
            """
            INSERT INTO nodes (
                node_id, role, organization, reputation_score, accuracy_score,
                private_key, active, validated_count, rejected_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(node_id) DO UPDATE SET
                role=excluded.role,
                organization=excluded.organization,
                reputation_score=excluded.reputation_score,
                accuracy_score=excluded.accuracy_score,
                private_key=excluded.private_key,
                active=excluded.active,
                validated_count=excluded.validated_count,
                rejected_count=excluded.rejected_count,
                created_at=excluded.created_at
            """,
            (
                node["node_id"],
                role,
                node["organization"],
                node["reputation_score"],
                node["accuracy_score"],
                node["private_key"],
                int(bool(node["active"])),
                node["validated_count"],
                node["rejected_count"],
                node["created_at"],
            ),
        )

    def load_transactions(self) -> List[Dict]:
        rows = self._fetch_all("SELECT * FROM transactions ORDER BY timestamp ASC")
        for row in rows:
            row["metadata"] = self._load(row.pop("metadata_json"), {})
        return rows

    def save_transaction(self, tx: Dict) -> None:
        self._execute(
            """
            INSERT INTO transactions (
                tx_id, trial_id, node_id, data_hash, ipfs_cid, metadata_json,
                timestamp, signature, status, ml_result, ml_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tx_id) DO UPDATE SET
                trial_id=excluded.trial_id,
                node_id=excluded.node_id,
                data_hash=excluded.data_hash,
                ipfs_cid=excluded.ipfs_cid,
                metadata_json=excluded.metadata_json,
                timestamp=excluded.timestamp,
                signature=excluded.signature,
                status=excluded.status,
                ml_result=excluded.ml_result,
                ml_confidence=excluded.ml_confidence
            """,
            (
                tx["tx_id"],
                tx["trial_id"],
                tx["node_id"],
                tx["data_hash"],
                tx.get("ipfs_cid", ""),
                self._dump(tx.get("metadata", {})),
                tx["timestamp"],
                tx.get("signature"),
                tx.get("status", "PENDING"),
                tx.get("ml_result"),
                tx.get("ml_confidence"),
            ),
        )

    def update_transaction_status(self, tx_id: str, status: str) -> None:
        self._execute("UPDATE transactions SET status = ? WHERE tx_id = ?", (status, tx_id))

    def load_governance_snapshots(self) -> List[Dict]:
        rows = self._fetch_all("SELECT * FROM governance_snapshots ORDER BY timestamp ASC")
        for row in rows:
            row["node_stats"] = self._load(row.pop("node_stats_json"), {})
        return rows

    def save_governance_snapshot(self, snapshot: Dict) -> None:
        self._execute(
            """
            INSERT INTO governance_snapshots (
                timestamp, pending_tx_count, avg_approval_ms, tps,
                model_accuracy, node_stats_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot["timestamp"],
                snapshot["pending_tx_count"],
                snapshot["avg_approval_ms"],
                snapshot["tps"],
                snapshot["model_accuracy"],
                self._dump(snapshot.get("node_stats", {})),
            ),
        )

    def load_governance_actions(self) -> List[Dict]:
        return self._fetch_all("SELECT * FROM governance_actions ORDER BY timestamp ASC")

    def save_governance_action(self, action: Dict) -> None:
        self._execute(
            """
            INSERT INTO governance_actions (
                action_type, target_node, delta, reason, timestamp
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                action["action_type"],
                action.get("target_node"),
                action["delta"],
                action["reason"],
                action["timestamp"],
            ),
        )

    def load_rejected_datasets(self) -> List[Dict]:
        rows = self._fetch_all("SELECT * FROM rejected_datasets ORDER BY submitted_at ASC")
        for row in rows:
            row["rows"] = self._load(row.pop("rows_json"), [])
            row["screening"] = self._load(row.pop("screening_json"), {})
            row["balance_report"] = self._load(row.pop("balance_report_json"), {})
            row["columns"] = self._load(row.pop("columns_json"), [])
            row["tx_ids"] = self._load(row.pop("tx_ids_json"), [])
        return rows

    def save_rejected_dataset(self, dataset: Dict) -> None:
        self._execute(
            """
            INSERT INTO rejected_datasets (
                id, filename, submitted_at, status, total_rows, flagged_rows,
                flagged_rate_pct, rows_json, screening_json, balance_report_json,
                columns_json, approved_by, approved_at, approval_note, tx_ids_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                filename=excluded.filename,
                submitted_at=excluded.submitted_at,
                status=excluded.status,
                total_rows=excluded.total_rows,
                flagged_rows=excluded.flagged_rows,
                flagged_rate_pct=excluded.flagged_rate_pct,
                rows_json=excluded.rows_json,
                screening_json=excluded.screening_json,
                balance_report_json=excluded.balance_report_json,
                columns_json=excluded.columns_json,
                approved_by=excluded.approved_by,
                approved_at=excluded.approved_at,
                approval_note=excluded.approval_note,
                tx_ids_json=excluded.tx_ids_json
            """,
            (
                dataset["id"],
                dataset["filename"],
                dataset["submitted_at"],
                dataset["status"],
                dataset["total_rows"],
                dataset["flagged_rows"],
                dataset["flagged_rate_pct"],
                self._dump(dataset.get("rows", [])),
                self._dump(dataset.get("screening", {})),
                self._dump(dataset.get("balance_report", {})),
                self._dump(dataset.get("columns", [])),
                dataset.get("approved_by"),
                dataset.get("approved_at"),
                dataset.get("approval_note"),
                self._dump(dataset.get("tx_ids", [])),
            ),
        )

    def delete_rejected_dataset(self, rejection_id: str) -> None:
        self._execute("DELETE FROM rejected_datasets WHERE id = ?", (rejection_id,))

    def load_ipfs_links(self) -> List[Dict]:
        rows = self._fetch_all("SELECT * FROM ipfs_link_records ORDER BY id ASC")
        for row in rows:
            row["record"] = self._load(row.pop("record_json"), {})
        return rows

    def save_ipfs_link(self, record: Dict) -> None:
        self._execute(
            """
            INSERT INTO ipfs_link_records (
                trial_id, ipfs_cid, sha256_hash, timestamp, uploader_node_id, record_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record["trial_id"],
                record["ipfs_cid"],
                record["sha256_hash"],
                record["timestamp"],
                record["uploader_node_id"],
                self._dump(record.get("record", {})),
            ),
        )