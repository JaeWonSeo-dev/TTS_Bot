from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EXPORTS_DIR = ROOT_DIR / "exports"
TRAINED_VOICES_DIR = ROOT_DIR / "trained_voices"
MODELS_DIR = ROOT_DIR / "models"


def build_training_command(prepared_dir: Path, output_dir: Path, base_model: str) -> list[str]:
    return [
        "python",
        "-m",
        "TTS.bin.train_tts",
        "--config_path",
        str(MODELS_DIR / "xtts_finetune_config.json"),
        "--coqpit.output_path",
        str(output_dir),
        "--coqpit.datasets.0.path",
        str(prepared_dir),
        "--coqpit.restore_path",
        base_model,
    ]


def train_voice(voice_id: str, base_model: str, execute: bool) -> int:
    prepared_dir = EXPORTS_DIR / voice_id / "dataset"
    if not prepared_dir.exists():
        print(f"[ERROR] prepared dataset not found: {prepared_dir}")
        print("[HINT] run prepare_dataset.py first")
        return 1

    output_dir = TRAINED_VOICES_DIR / voice_id / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    command = build_training_command(prepared_dir, output_dir, base_model)

    metadata = {
        "voice_id": voice_id,
        "prepared_dir": str(prepared_dir),
        "output_dir": str(output_dir),
        "base_model": base_model,
        "execute": execute,
        "command": command,
        "created_at": datetime.now().isoformat(),
        "status": "planned",
    }

    metadata_path = output_dir / "training_run.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[INFO] training command")
    print(" ".join(command))
    print(f"[INFO] run metadata saved to: {metadata_path}")

    if not execute:
        print("[INFO] dry-run only. add --execute to actually start training")
        return 0

    env = os.environ.copy()
    try:
        process = subprocess.run(command, cwd=str(ROOT_DIR), env=env, check=False)
    except FileNotFoundError as exc:
        print(f"[ERROR] failed to launch training command: {exc}")
        return 1

    status = "finished" if process.returncode == 0 else "failed"
    metadata["status"] = status
    metadata["return_code"] = process.returncode
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[RESULT] training {status} (code={process.returncode})")
    return process.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Train/fine-tune a speaker voice")
    parser.add_argument("--voice-id", required=True)
    parser.add_argument("--base-model", default="models/xtts_v2/model.pth")
    parser.add_argument("--execute", action="store_true", help="actually launch the training command")
    args = parser.parse_args()
    return train_voice(args.voice_id, args.base_model, args.execute)


if __name__ == "__main__":
    sys.exit(main())
