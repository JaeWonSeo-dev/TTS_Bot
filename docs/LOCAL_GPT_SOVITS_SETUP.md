# Local GPT-SoVITS Setup

목표: **샘플 음성만 준비되면 바로 보이스 클로닝 테스트/학습 준비를 진행할 수 있는 상태**까지 로컬 PC 기준으로 맞춘다.

## 1. 현재 프로젝트 기준 준비된 것

이 프로젝트(`TTS_Bot`)에는 이미 아래가 준비되어 있다.

- Discord 봇에서 `gpt_sovits` 엔진 선택 가능
- `voice_samples/<voice_id>/ref.wav` 구조 인식 가능
- `prompt.txt` / `speaker.json` 기반 화자 메타 인식 가능
- `scripts/check_gpt_sovits_api.py`로 로컬 API 상태 확인 가능
- `scripts/check_local_gpt_sovits_setup.py`로 로컬 GPT-SoVITS 설치 상태 확인 가능
- `scripts/start_local_gpt_sovits_api.ps1`로 로컬 API 실행 래퍼 사용 가능
- `training/ingest_samples.py` → `validate_dataset.py` → `prepare_dataset.py` 흐름 준비됨

추가로 공식 GPT-SoVITS 저장소를 아래 경로에 내려받아 두었다.

```text
C:\Sjw_dev\Coding\GPT-SoVITS
```

## 2. 로컬 폴더 구조

예시:

```text
voice_samples/
  jaewon/
    ref.wav
    prompt.txt
    speaker.json
    clip_001.wav
    clip_001.txt
    clip_002.wav
```

### 파일 의미
- `ref.wav`: GPT-SoVITS 추론용 대표 참조 음성
- `prompt.txt`: `ref.wav` 안에서 실제로 말한 문장
- `speaker.json`: 언어/프롬프트 메타 정보
- `clip_001.wav`, `clip_001.txt`: 학습 데이터셋 입력용 raw 샘플

## 3. 화자 폴더 템플릿 만들기

```bash
python scripts/bootstrap_voice_sample.py jaewon --language ko --prompt-text "안녕하세요. 저는 테스트용 샘플 화자입니다."
```

생성 결과:

```text
voice_samples/jaewon/
  prompt.txt
  speaker.json
  README.txt
```

그 다음 네가 해야 할 것:
- `ref.wav` 넣기
- `prompt.txt`를 실제 발화 문장으로 수정
- 필요하면 `clip_001.wav`, `clip_001.txt` 쌍 추가

## 4. 로컬 GPT-SoVITS 서버 확인

기본 URL은 아래로 잡혀 있다.

```text
http://127.0.0.1:9880/tts
```

설치 상태 확인:

```bash
python scripts/check_local_gpt_sovits_setup.py
```

현재 기준 체크 포인트:
- 공식 repo clone 완료: `C:\Sjw_dev\Coding\GPT-SoVITS`
- API 기본 포트: `127.0.0.1:9880`
- 아직 로컬 API 프로세스는 실행 전일 수 있음

PowerShell에서 API 실행:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_local_gpt_sovits_api.ps1
```

필요하면 경로를 직접 지정:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_local_gpt_sovits_api.ps1 -RepoDir "C:\Sjw_dev\Coding\GPT-SoVITS" -PythonExe "python" -BindAddress "127.0.0.1" -Port 9880
```

상태 확인:

```bash
python scripts/check_gpt_sovits_api.py --url http://127.0.0.1:9880/tts --method GET
```

샘플이 준비된 뒤 POST 테스트:

```bash
python scripts/check_gpt_sovits_api.py --method POST --url http://127.0.0.1:9880/tts --voice-ref voice_samples/jaewon/ref.wav --prompt-text "안녕하세요. 저는 테스트용 샘플 화자입니다." --text "안녕하세요. 연결 테스트입니다."
```

## 5. 봇 환경 변수

`.env` 예시:

```env
TTS_ENGINE=gpt_sovits
TTS_VOICE=jaewon
GPT_SOVITS_API_URL=http://127.0.0.1:9880/tts
```

## 6. 학습 준비 흐름

샘플이 준비되면 순서는 아래와 같다.

### 6-1. raw 샘플 ingest

```bash
python training/ingest_samples.py --voice-id jaewon --language ko --auto-transcribe
```

### 6-2. dataset 검증

```bash
python training/validate_dataset.py --voice-id jaewon
```

### 6-3. training용 export 준비

```bash
python training/prepare_dataset.py --voice-id jaewon
```

## 7. 현재 한계 / 체크 포인트

- 공식 GPT-SoVITS repo는 로컬에 clone해 두었지만, 모델 다운로드/환경 설치/실제 서버 기동은 아직 별도 진행이 필요하다.
- 현재 머신에서는 `conda`가 바로 잡히지 않았으므로, 공식 설치 스크립트 실행 전에는 Python/torch 환경을 따로 맞출 필요가 있을 수 있다.
- 그래서 현재 프로젝트는 **샘플 투입 전 준비 + 학습 전처리/정리 단계까지는 바로 진행 가능**하고,
  **최종 학습 실행/실제 API 기동은 네 로컬 GPT-SoVITS 환경이 준비된 뒤 맞춤 연결**하는 방식이 안전하다.
- 즉, 지금 상태는 **샘플만 생기면 화자 폴더 정리, 데이터셋 생성/검증/준비, API 연결 테스트까지 바로 가능한 상태**다.
