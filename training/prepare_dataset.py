from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATASETS_DIR = ROOT_DIR / "datasets"
EXPORTS_DIR = ROOT_DIR / "exports"


def prepare_dataset(voice_id: str) -> int:
    dataset_dir = DATASETS_DIR / voice_id
    wavs_dir = dataset_dir / "wavs"
    metadata_path = dataset_dir / "metadata.csv"

    if not dataset_dir.exists() or not wavs_dir.exists() or not metadata_path.exists():
        print("[ERROR] dataset structure is incomplete")
        return 1

    export_dir = EXPORTS_DIR / voice_id / "dataset"
    export_wavs_dir = export_dir / "wavs"
    export_wavs_dir.mkdir(parents=True, exist_ok=True)

    rows: list[list[str]] = []
    with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="|")
        for row in reader:
            if row:
                rows.append(row)

    normalized_rows: list[str] = []
    for row in rows:
        file_name = row[0].strip()
        text = row[1].strip()
        source_wav = wavs_dir / file_name
        target_wav = export_wavs_dir / file_name
        if not source_wav.exists():
            print(f"[ERROR] missing wav: {source_wav}")
            return 1
        shutil.copy2(source_wav, target_wav)
        normalized_rows.append(f"wavs/{file_name}|{text}")

    (export_dir / "metadata.csv").write_text("\n".join(normalized_rows) + "\n", encoding="utf-8")

    speaker_json = dataset_dir / "speaker.json"
    if speaker_json.exists():
        shutil.copy2(speaker_json, export_dir / "speaker.json")

    manifest = {
        "voice_id": voice_id,
        "dataset_dir": str(dataset_dir),
        "prepared_dir": str(export_dir),
        "utterance_count": len(normalized_rows),
    }
    (export_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] prepared dataset at: {export_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare dataset for training")
    parser.add_argument("--voice-id", required=True)
    args = parser.parse_args()
    return prepare_dataset(args.voice_id)


if __name__ == "__main__":
    sys.exit(main())
