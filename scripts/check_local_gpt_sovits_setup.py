from __future__ import annotations

import argparse
import json
import os
import socket
from pathlib import Path


DEFAULT_REPO = Path(r"C:\Sjw_dev\Coding\GPT-SoVITS")
DEFAULT_API_URL = "http://127.0.0.1:9880/tts"


def port_open(host: str, port: int, timeout: float = 1.5) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local GPT-SoVITS setup status")
    parser.add_argument("--repo-dir", default=str(DEFAULT_REPO))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9880)
    args = parser.parse_args()

    repo_dir = Path(args.repo_dir)
    status = {
        "repo_dir": str(repo_dir),
        "repo_exists": repo_dir.exists(),
        "api_v2_exists": (repo_dir / "api_v2.py").exists(),
        "tts_config_exists": (repo_dir / "GPT_SoVITS" / "configs" / "tts_infer.yaml").exists(),
        "api_url": DEFAULT_API_URL.replace("127.0.0.1:9880", f"{args.host}:{args.port}"),
        "port_open": port_open(args.host, args.port),
        "notes": [],
    }

    if not status["repo_exists"]:
        status["notes"].append("GPT-SoVITS repo is missing")
    if status["repo_exists"] and not status["api_v2_exists"]:
        status["notes"].append("api_v2.py is missing")
    if status["repo_exists"] and not status["tts_config_exists"]:
        status["notes"].append("GPT_SoVITS/configs/tts_infer.yaml is missing")
    if not status["port_open"]:
        status["notes"].append("GPT-SoVITS API port is not accepting connections yet")

    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
