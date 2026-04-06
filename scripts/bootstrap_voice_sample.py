from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
VOICE_SAMPLES_DIR = ROOT_DIR / "voice_samples"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a GPT-SoVITS voice sample folder template")
    parser.add_argument("voice_id")
    parser.add_argument("--language", default="ko")
    parser.add_argument("--prompt-text", default="안녕하세요. 저는 테스트용 샘플 화자입니다.")
    args = parser.parse_args()

    target_dir = VOICE_SAMPLES_DIR / args.voice_id
    target_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = target_dir / "prompt.txt"
    if not prompt_path.exists():
        prompt_path.write_text(args.prompt_text + "\n", encoding="utf-8")

    speaker_path = target_dir / "speaker.json"
    if not speaker_path.exists():
        speaker_path.write_text(
            json.dumps(
                {
                    "prompt_text": args.prompt_text,
                    "prompt_language": args.language,
                    "text_language": args.language,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    readme_path = target_dir / "README.txt"
    if not readme_path.exists():
        readme_path.write_text(
            "Put ref.wav here and replace prompt.txt with the exact spoken sentence from ref.wav.\n"
            "Optional training clips can also go here as clip_001.wav + clip_001.txt pairs.\n",
            encoding="utf-8",
        )

    print(f"[OK] template ready: {target_dir}")
    print(f"[NEXT] put ref.wav at: {target_dir / 'ref.wav'}")
    print(f"[NEXT] update prompt.txt to match the actual spoken words in ref.wav")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
