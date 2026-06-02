"""
Local runtime configuration for the clinical-trial blockchain prototype.

Values come from environment variables, with defaults that make the app run
locally without extra setup. python-dotenv is optional but supported.
"""
import os
from pathlib import Path
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is listed in requirements
    load_dotenv = None

if load_dotenv:
    load_dotenv()


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    backend_host: str = _env("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(_env("BACKEND_PORT", _env("PORT", "8000")))
    cors_origins: str = _env("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    uvicorn_reload: bool = _env("UVICORN_RELOAD", "false").lower() == "true"
    sqlite_db_path: str = _env(
        "SQLITE_DB_PATH",
        str(Path(__file__).resolve().parent.parent / "data" / "ledger.sqlite3"),
    )

    ipfs_api_url: str = _env("IPFS_API_URL", "/ip4/127.0.0.1/tcp/5001")
    hardhat_rpc_url: str = _env("HARDHAT_RPC_URL", "http://127.0.0.1:8545")
    contract_address: str = _env("CONTRACT_ADDRESS", "")


settings = Settings()
