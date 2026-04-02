# Voice Samples

이 폴더는 **A 방식 참조 음성** 또는 샘플 mp3/wav를 보관하는 용도야.

## A 방식 참조 음성 예시

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

## B 방식과의 차이

- `voice_samples/` : 즉시 참조 복제용 샘플
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
