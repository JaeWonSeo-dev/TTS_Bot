import asyncio
from pathlib import Path

import edge_tts


SAMPLES = {
    "ko_female_1": "ko-KR-SunHiNeural",
    "ko_female_2": "ko-KR-JiMinNeural",
    "ko_male_1": "ko-KR-InJoonNeural",
    "ko_male_2": "ko-KR-BongJinNeural",
    "en_female_1": "en-US-JennyNeural",
    "en_male_1": "en-US-GuyNeural",
}

SAMPLE_TEXT = {
    "ko": "안녕하세요. 이 파일은 디스코드 TTS 봇의 음성 샘플입니다.",
    "en": "Hello. This is a voice sample for the Discord TTS bot.",
}


async def main() -> None:
    root = Path(__file__).resolve().parent.parent
    output_dir = root / "voice_samples"
    output_dir.mkdir(parents=True, exist_ok=True)

    for voice_id, provider_voice in SAMPLES.items():
        text = SAMPLE_TEXT["ko"] if provider_voice.startswith("ko-") else SAMPLE_TEXT["en"]
        output_path = output_dir / f"{voice_id}.mp3"
        communicate = edge_tts.Communicate(text=text, voice=provider_voice)
        await communicate.save(str(output_path))
        print(f"generated: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
