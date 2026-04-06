# Voice Samples

이 폴더는 **A 방식 참조 음성** 또는 샘플 mp3/wav를 보관하는 용도야.

## GPT-SoVITS용 권장 구조

```text
voice_samples/
  jaewon/
    ref.wav
    prompt.txt
    speaker.json   # 선택
```

- `ref.wav`: 대표 참조 음성
- `prompt.txt`: `ref.wav` 안에서 실제로 말한 문장
- `speaker.json`: 선택. `prompt_text`, `prompt_language`, `text_language` 저장 가능

예시:

```json
{
  "prompt_text": "안녕하세요. 저는 테스트용 샘플 화자입니다.",
  "prompt_language": "ko",
  "text_language": "ko"
}
```

## XTTS용 간단 구조

```text
voice_samples/
  jaewon/
    ref.wav
```

또는:

```text
voice_samples/
  jaewon.wav
```

## B 방식 raw 입력 경로

이제 학습용 raw 샘플도 여기에서 바로 시작할 수 있어.

예:

```text
voice_samples/
  jaewon/
    clip_001.wav
    clip_001.txt
    clip_002.wav
```

그 뒤 아래 명령으로 dataset 구조를 자동 생성:

```bash
python training/ingest_samples.py --voice-id jaewon --language ko --auto-transcribe
```

## B 방식과의 차이

- `voice_samples/` : 즉시 참조 복제용 샘플 + 학습용 raw 입력 시작점
- `datasets/` : 학습용 화자 데이터셋

기본 추천 샘플 보이스(Edge):
- ko_female_1 -> ko-KR-SunHiNeural
- ko_female_2 -> ko-KR-JiMinNeural
- ko_male_1 -> ko-KR-InJoonNeural
- ko_male_2 -> ko-KR-BongJinNeural
- en_female_1 -> en-US-JennyNeural
- en_male_1 -> en-US-GuyNeural

샘플 생성은 `scripts/generate_voice_samples.py`로 할 수 있어.
생성된 mp3는 이 폴더에 저장돼.
