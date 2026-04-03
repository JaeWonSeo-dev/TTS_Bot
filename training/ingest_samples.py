from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import soundfile as sf


ROOT_DIR = Path(__file__).resolve().parents[1]
VOICE_SAMPLES_DIR = ROOT_DIR / "voice_samples"
DATASETS_DIR = ROOT_DIR / "datasets"

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".flac", ".mp3", ".m4a", ".ogg"}


@dataclass
class SampleItem:
    source_audio_path: Path
    target_file_name: str
    transcript: str
    duration_sec: float
    transcript_source: str


def normalize_text(text: str) -> str:
    return " ".join(text.replace("\n", " ").split()).strip()


def get_duration_sec(path: Path) -> float:
    return round(float(sf.info(str(path)).duration), 2)


def transcribe_with_whisper(audio_path: Path, language: str, model_size: str, device: str, compute_type: str) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("faster-whisper is not installed. Run `pip install -r requirements.txt`.") from exc

    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, _ = model.transcribe(str(audio_path), language=language, vad_filter=True)
    text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
    return normalize_text(text)


def collect_samples(
    voice_id: str,
    language: str,
    auto_transcribe: bool,
    whisper_model: str,
    whisper_device: str,
    whisper_compute_type: str,
    min_clip_sec: float,
    max_clip_sec: float,
) -> list[SampleItem]:
    source_dir = VOICE_SAMPLES_DIR / voice_id
    if not source_dir.exists() or not source_dir.is_dir():
        raise RuntimeError(f"sample folder not found: {source_dir}")

    collected: list[SampleItem] = []
    index = 1
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
            continue
        if path.name.lower() == "ref.wav":
            continue

        duration_sec = get_duration_sec(path)
        if duration_sec < min_clip_sec or duration_sec > max_clip_sec:
            continue

        txt_path = path.with_suffix(".txt")
        transcript_source = "txt"
        if txt_path.exists():
            transcript = normalize_text(txt_path.read_text(encoding="utf-8"))
        elif auto_transcribe:
            transcript = transcribe_with_whisper(path, language, whisper_model, whisper_device, whisper_compute_type)
            transcript_source = "whisper"
        else:
            continue

        if not transcript:
            continue

        target_file_name = f"{index:04d}.wav"
        collected.append(
            SampleItem(
                source_audio_path=path,
                target_file_name=target_file_name,
                transcript=transcript,
                duration_sec=duration_sec,
                transcript_source=transcript_source,
            )
        )
        index += 1

    return collected


def ingest_samples(
    voice_id: str,
    language: str,
    display_name: str | None,
    auto_transcribe: bool,
    whisper_model: str,
    whisper_device: str,
    whisper_compute_type: str,
    min_clip_sec: float,
    max_clip_sec: float,
) -> int:
    samples = collect_samples(
        voice_id=voice_id,
        language=language,
        auto_transcribe=auto_transcribe,
        whisper_model=whisper_model,
        whisper_device=whisper_device,
        whisper_compute_type=whisper_compute_type,
        min_clip_sec=min_clip_sec,
        max_clip_sec=max_clip_sec,
    )

    if not samples:
        print("[ERROR] no usable samples found")
        print(f"[HINT] put audio files under {VOICE_SAMPLES_DIR / voice_id}")
        return 1

    dataset_dir = DATASETS_DIR / voice_id
    wavs_dir = dataset_dir / "wavs"
    wavs_dir.mkdir(parents=True, exist_ok=True)

    metadata_rows: list[list[str]] = []
    auto_transcribed_count = 0
    total_duration = 0.0

    for sample in samples:
        target_wav = wavs_dir / sample.target_file_name
        audio, sample_rate = sf.read(str(sample.source_audio_path))
        sf.write(str(target_wav), audio, sample_rate)
        metadata_rows.append([sample.target_file_name, sample.transcript])
        total_duration += sample.duration_sec
        if sample.transcript_source == "whisper":
            auto_transcribed_count += 1

    metadata_path = dataset_dir / "metadata.csv"
    with metadata_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="|")
        writer.writerows(metadata_rows)

    speaker = {
        "voice_id": voice_id,
        "display_name": display_name or voice_id,
        "language": language,
        "description": f"ingested from {VOICE_SAMPLES_DIR / voice_id}",
    }
    speaker_path = dataset_dir / "speaker.json"
    speaker_path.write_text(json.dumps(speaker, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "voice_id": voice_id,
        "source_dir": str(VOICE_SAMPLES_DIR / voice_id),
        "dataset_dir": str(dataset_dir),
        "utterance_count": len(samples),
        "total_duration_sec": round(total_duration, 2),
        "auto_transcribed_count": auto_transcribed_count,
        "metadata_path": str(metadata_path),
        "speaker_path": str(speaker_path),
    }
    summary_path = dataset_dir / "ingest_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] dataset created: {dataset_dir}")
    print(f"[INFO] utterance_count: {len(samples)}")
    print(f"[INFO] total_duration_sec: {total_duration:.2f}")
    print(f"[INFO] auto_transcribed_count: {auto_transcribed_count}")
    print(f"[INFO] metadata: {metadata_path}")
    print(f"[INFO] summary: {summary_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest raw voice samples into datasets/<voice_id>")
    parser.add_argument("--voice-id", required=True)
    parser.add_argument("--language", default="ko", choices=["ko", "en"])
    parser.add_argument("--display-name", default=None)
    parser.add_argument("--auto-transcribe", action="store_true")
    parser.add_argument("--whisper-model", default="small")
    parser.add_argument("--whisper-device", default="cuda")
    parser.add_argument("--whisper-compute-type", default="float16")
    parser.add_argument("--min-clip-sec", type=float, default=3.0)
    parser.add_argument("--max-clip-sec", type=float, default=20.0)
    args = parser.parse_args()
    return ingest_samples(
        voice_id=args.voice_id,
        language=args.language,
        display_name=args.display_name,
        auto_transcribe=args.auto_transcribe,
        whisper_model=args.whisper_model,
        whisper_device=args.whisper_device,
        whisper_compute_type=args.whisper_compute_type,
        min_clip_sec=args.min_clip_sec,
        max_clip_sec=args.max_clip_sec,
    )


if __name__ == "__main__":
    sys.exit(main())
