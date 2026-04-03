# B 방식 학습 가이드

이 프로젝트의 B 방식 목표는 **화자별 데이터셋을 등록하고, 이후 그 화자 목소리로 안정적으로 TTS를 생성할 수 있는 구조**를 만드는 것이다.

## 가장 간단한 시작 방법

원본 샘플만 먼저 아래 경로에 넣어도 된다.

```text
voice_samples/
  jaewon/
    clip_001.wav
    clip_001.txt
    clip_002.wav
    clip_003.wav
```

그 다음 아래 순서로 실행하면 된다.

```bash
python training/ingest_samples.py --voice-id jaewon --language ko --auto-transcribe
python training/validate_dataset.py --voice-id jaewon
python training/prepare_dataset.py --voice-id jaewon
python training/train_voice.py --voice-id jaewon
```

- `.txt`가 있으면 그 전사를 우선 사용
- `.txt`가 없으면 `--auto-transcribe`로 Whisper 자동 전사
- `ingest_samples.py`가 `datasets/<voice_id>/` 구조를 자동 생성

## 권장 데이터셋 구조

```text
datasets/
  jaewon/
    wavs/
      0001.wav
      0002.wav
      0003.wav
    metadata.csv
    speaker.json
```

### metadata.csv 형식

```csv
0001.wav|안녕하세요. 테스트용 음성입니다.
0002.wav|이 데이터는 화자 학습을 위한 샘플입니다.
0003.wav|한국어와 영어를 모두 읽을 수 있게 준비합니다.
```

### speaker.json 예시

```json
{
  "voice_id": "jaewon",
  "display_name": "JaeWon",
  "language": "ko",
  "description": "clean indoor recording"
}
```

## 권장 녹음 조건

- WAV
- 16bit PCM 권장
- mono 권장
- 22050 / 24000 / 44100 Hz 중 하나로 통일 권장
- 파일당 3~12초 정도 권장
- 한 사람만 말해야 함
- 배경음악, 에코, 심한 잡음 제거

## 최소 권장 분량

- 실험 최소: 5~10분
- 권장 시작: 20~30분
- 안정적 운영 목표: 40분~1시간 이상

## 운영 관점 권장 구조

- `datasets/`: 원본/정제 데이터
- `training/`: 검증/전처리/학습 스크립트
- `trained_voices/`: 학습 결과물 메타와 체크포인트 위치
- `models/`: 공통 베이스 모델 또는 다운로드 위치
- `exports/`: 배포용 산출물

## 핵심 원칙

1. 학습 전에 데이터셋 검증
2. 화자별로 폴더 완전 분리
3. 학습 로그와 결과 메타를 남길 것
4. 원본 음성과 학습 산출물을 섞지 말 것
