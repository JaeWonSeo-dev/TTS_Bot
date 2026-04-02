from __future__ import annotations

import argparse
import csv
import json
import sys
import wave
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATASETS_DIR = ROOT_DIR / "datasets"


@dataclass
class ValidationIssue:
    level: str
    message: str


@dataclass
class AudioInfo:
    sample_rate: int
    channels: int
    frames: int
    duration_sec: float


def load_audio_info(path: Path) -> AudioInfo:
    with wave.open(str(path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()
        frames = wav_file.getnframes()
    duration_sec = frames / sample_rate if sample_rate else 0.0
    return AudioInfo(sample_rate=sample_rate, channels=channels, frames=frames, duration_sec=duration_sec)


def read_metadata(metadata_path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="|")
        for row in reader:
            if not row:
                continue
            if len(row) < 2:
                raise ValueError(f"metadata row must be 'filename|text': {row}")
            rows.append((row[0].strip(), row[1].strip()))
    return rows


def validate_dataset(voice_id: str) -> int:
    dataset_dir = DATASETS_DIR / voice_id
    wavs_dir = dataset_dir / "wavs"
    metadata_path = dataset_dir / "metadata.csv"
    speaker_path = dataset_dir / "speaker.json"

    issues: list[ValidationIssue] = []

    if not dataset_dir.exists():
        print(f"[ERROR] dataset not found: {dataset_dir}")
        return 1
    if not wavs_dir.exists():
        print(f"[ERROR] wavs directory not found: {wavs_dir}")
        return 1
    if not metadata_path.exists():
        print(f"[ERROR] metadata.csv not found: {metadata_path}")
        return 1

    if speaker_path.exists():
        try:
            json.loads(speaker_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(ValidationIssue("ERROR", f"speaker.json parse failed: {exc}"))

    try:
        rows = read_metadata(metadata_path)
    except Exception as exc:
        print(f"[ERROR] failed to read metadata: {exc}")
        return 1

    if not rows:
        issues.append(ValidationIssue("ERROR", "metadata.csv is empty"))

    total_duration = 0.0
    sample_rates: set[int] = set()
    channel_counts: set[int] = set()

    for file_name, text in rows:
        wav_path = wavs_dir / file_name
        if not wav_path.exists():
            issues.append(ValidationIssue("ERROR", f"missing wav file referenced in metadata: {file_name}"))
            continue
        if not text:
            issues.append(ValidationIssue("ERROR", f"empty transcript: {file_name}"))
            continue

        try:
            info = load_audio_info(wav_path)
        except wave.Error as exc:
            issues.append(ValidationIssue("ERROR", f"invalid wav file {file_name}: {exc}"))
            continue

        total_duration += info.duration_sec
        sample_rates.add(info.sample_rate)
        channel_counts.add(info.channels)

        if info.duration_sec < 1.0:
            issues.append(ValidationIssue("WARN", f"very short audio (<1s): {file_name}"))
        if info.duration_sec > 15.0:
            issues.append(ValidationIssue("WARN", f"long audio (>15s): {file_name}"))
        if info.channels != 1:
            issues.append(ValidationIssue("WARN", f"not mono: {file_name} ({info.channels} channels)"))

    wav_files = {path.name for path in wavs_dir.glob("*.wav")}
    metadata_files = {file_name for file_name, _ in rows}
    extra_wavs = sorted(wav_files - metadata_files)
    for file_name in extra_wavs:
        issues.append(ValidationIssue("WARN", f"wav exists but not referenced in metadata: {file_name}"))

    print(f"[INFO] dataset: {voice_id}")
    print(f"[INFO] utterances: {len(rows)}")
    print(f"[INFO] total_duration_sec: {total_duration:.2f}")
    print(f"[INFO] total_duration_min: {total_duration / 60:.2f}")
    print(f"[INFO] sample_rates: {sorted(sample_rates)}")
    print(f"[INFO] channel_counts: {sorted(channel_counts)}")

    if total_duration < 300:
        issues.append(ValidationIssue("WARN", "dataset is under 5 minutes; only suitable for limited experiments"))
    if total_duration < 1200:
        issues.append(ValidationIssue("WARN", "dataset is under 20 minutes; quality may be unstable for production"))
    if len(sample_rates) > 1:
        issues.append(ValidationIssue("WARN", "mixed sample rates detected; normalize before training"))

    error_count = 0
    for issue in issues:
        print(f"[{issue.level}] {issue.message}")
        if issue.level == "ERROR":
            error_count += 1

    if error_count:
        print(f"[RESULT] failed with {error_count} error(s)")
        return 1

    print("[RESULT] validation passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a speaker training dataset")
    parser.add_argument("--voice-id", required=True, help="dataset folder name under datasets/")
    args = parser.parse_args()
    return validate_dataset(args.voice_id)


if __name__ == "__main__":
    sys.exit(main())
