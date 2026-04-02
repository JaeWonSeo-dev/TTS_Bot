# Training

B 방식(학습 기반 화자 등록)용 스크립트 모음.

## 흐름

1. `datasets/<voice_id>/wavs/*.wav` 준비
2. `datasets/<voice_id>/metadata.csv` 준비
3. `python training/validate_dataset.py --voice-id <voice_id>`
4. `python training/prepare_dataset.py --voice-id <voice_id>`
5. `python training/train_voice.py --voice-id <voice_id>`
6. 생성된 결과를 `trained_voices/<voice_id>/`에서 확인

## 주의

- 현재 `train_voice.py`는 **실전용 학습 실행 뼈대**와 결과물 메타 저장까지 포함한다.
- XTTS/Coqui 학습 커맨드는 환경마다 달라질 수 있어서, 기본은 dry-run 설명 + 명령 생성 방식으로 넣어뒀다.
- 실제 GPU 학습 전에는 반드시 `validate_dataset.py`를 먼저 돌려서 데이터셋을 점검해야 한다.
