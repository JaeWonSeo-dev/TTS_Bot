# Discord TTS Bot

디스코드 음성 채널에서 실제로 쓸 수 있는 수준의 TTS 봇이야.
이 버전의 기본 구조는 **먼저 텍스트 채널을 지정하고**, 그 채널에 메시지를 쓴 사람이 들어가 있는 **음성채널로 봇이 자동 이동해서 읽는 방식**이야.

## 핵심 동작 방식

1. 관리자가 TTS 대상 텍스트 채널 A를 지정함: `!setup`
2. 누군가가 채널 A에 메시지를 입력함
3. 그 사람이 음성채널에 들어가 있으면
4. 봇이 그 사람의 음성채널로 자동 이동/입장
5. 채널 A의 메시지를 TTS로 읽음

즉, 네가 말한 구조 그대로:
- **TTS 대상은 텍스트 채널 기준으로 먼저 정함**
- **출력 위치는 메시지를 친 사람이 있는 음성채널 기준으로 따라감**

## 기능

- `!join` : 수동으로 명령을 보낸 사용자의 음성 채널에 입장
- `!leave` : 음성 채널에서 퇴장하고 대기열 정리
- `!say <문장>` : 직접 TTS 재생
- `!setreadchannel [#채널]` / `!setup [#채널]` : 자동 읽기 채널 지정
- `!clearreadchannel` : 자동 읽기 채널 해제
- `!readchannel` : 현재 자동 읽기 채널 확인
- `!settings` : 현재 서버 설정 확인
- `!xsaid <on|off>` : 닉네임 먼저 읽기 여부 설정
- `!multilang <on|off>` : 한국어/영어 자동 판별 읽기 설정
- `!engines` : 사용 가능한 TTS 엔진 목록 확인
- `!voices [engine]` : 사용 가능한 보이스 목록 확인
- `!setengine <engine>` : TTS 엔진 변경
- `!setvoice <voice_id>` : 보이스 변경
- `!male` : 기본 남성 보이스로 빠르게 변경
- `!female` : 기본 여성 보이스로 빠르게 변경
- `!voice` : 현재 엔진/보이스 확인
- `!sample [voice_id] [문장]` : 샘플 보이스 재생
- `!skip` : 현재 재생 중인 음성 스킵
- `!stop` : 현재 재생 중인 음성 정지 + 대기열 비우기
- `!queue` : 현재 재생/대기 상태 확인
- `!ping` : 상태 확인

## 추천 초기 설정

```text
!setup
!female
!xsaid off
!multilang on
!settings
```

## 자동 읽기 방식 상세

- 지정된 텍스트 채널의 메시지만 읽음
- 메시지를 입력한 사용자가 음성채널에 없으면 읽지 않음
- 메시지를 입력한 사용자가 음성채널에 있으면 그 채널로 봇이 자동 이동함
- 명령어 메시지(`!`)는 자동 읽기에서 제외됨
- 봇 메시지는 읽지 않음
- 서버마다 설정이 따로 저장됨
- `xsaid`가 켜져 있으면 `닉네임 + 메시지` 형식으로 읽고, 꺼져 있으면 메시지만 읽음

## 한국어 / 영어 자동 읽기

- `multilang`가 켜져 있으면 메시지 내용을 보고 한국어/영어를 자동 판별해 읽어.
- 한국어가 포함되면 한국어 보이스를 우선 사용해.
- 영어만 있으면 영어 보이스를 사용해.
- 기본 매핑:
  - 한국어: `ko_female_1` -> `ko-KR-SunHiNeural`
  - 영어: `en_female_1` -> `en-US-JennyNeural`

## 엔진 / 보이스 설정

현재 기본 탑재 엔진:
- `edge` : Microsoft Edge TTS
- `xtts` : XTTS v2 기반 참조 음성 voice cloning TTS

기본 보이스 별칭:
- `ko_female_1` -> `ko-KR-SunHiNeural`
- `ko_female_2` -> `ko-KR-JiMinNeural`
- `ko_male_1` -> `ko-KR-InJoonNeural`
- `ko_male_2` -> `ko-KR-BongJinNeural`
- `en_female_1` -> `en-US-JennyNeural`
- `en_male_1` -> `en-US-GuyNeural`

### XTTS 화자 등록 방식

XTTS를 쓰려면 참조 음성을 아래처럼 넣으면 돼:

```text
voice_samples/
  jaewon/
    ref.wav
```

또는 단일 파일도 가능해:

```text
voice_samples/
  jaewon.wav
```

그 다음:

```text
!voices xtts
!setengine xtts
!setvoice jaewon
```

권장 참조 음성 조건:
- 10~60초 WAV
- 한 사람만 말하는 음성
- 배경음악 없음
- 잡음/에코 적음
- 한국어/영어 둘 다 가능

## B 방식 학습 구조

이제 프로젝트 안에 학습 기반 화자 등록을 위한 기본 골격도 들어 있다.

```text
datasets/
training/
models/
trained_voices/
exports/
docs/TRAINING_GUIDE.md
```

기본 흐름:

```bash
python training/ingest_samples.py --voice-id sample_speaker --language ko --auto-transcribe
python training/validate_dataset.py --voice-id sample_speaker
python training/prepare_dataset.py --voice-id sample_speaker
python training/train_voice.py --voice-id sample_speaker
```

이제 raw 샘플만 아래 경로에 넣어두면 dataset 생성까지 자동으로 만들 수 있다.

```text
voice_samples/
  sample_speaker/
    clip_001.wav
    clip_001.txt   # 있으면 우선 사용
    clip_002.wav   # txt 없으면 --auto-transcribe 시 Whisper 전사
```

`training/ingest_samples.py`가 다음을 자동 처리한다:
- `voice_samples/<voice_id>/` 스캔
- 길이 조건에 맞는 오디오 선별
- `.txt` 전사 우선 사용
- 없으면 Whisper 자동 전사
- `datasets/<voice_id>/wavs/*.wav` 생성
- `datasets/<voice_id>/metadata.csv` 생성
- `datasets/<voice_id>/speaker.json` 생성

즉, 실제 화자를 학습하려고 할 때 이제는 raw 샘플을 특정 경로에 넣고 `ingest_samples.py`만 돌리면 학습 시작 전 단계까지 준비된다.

## 설정 파일

서버별 설정은 아래 파일에 저장돼:

```text
data/guild_settings.json
```

예를 들면 다음 정보가 들어가:
- 자동 읽기 채널 ID
- TTS 엔진
- voice_id
- xsaid
- multilang

## 설치 및 실행

```bash
pip install -r requirements.txt
python main.py
```

`.env.example`을 복사해서 `.env`를 만들고 토큰/FFmpeg 경로를 넣으면 돼.
XTTS를 쓸 거면 첫 실행 전에 추가로 모델 다운로드 시간이 걸릴 수 있어.
디버깅이 필요하면 `DEBUG_LOG=true` 상태로 실행해서 콘솔 로그를 확인하면 돼.
