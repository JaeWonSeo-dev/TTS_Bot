# Discord TTS Bot

디스코드 음성 채널에서 실제로 쓸 수 있는 수준의 TTS 봇이야.
티토커 느낌의 기본 설정 흐름을 따라가면서, 한국어/영어 자동 읽기도 들어가 있어.

## 기능

- `!join` : 명령을 보낸 사용자가 있는 음성 채널에 입장
- `!leave` : 음성 채널에서 퇴장하고 대기열 정리
- `!say <문장>` : 직접 TTS 재생
- `!setreadchannel [#채널]` / `!setup [#채널]` : 자동 읽기 채널 지정
- `!clearreadchannel` : 자동 읽기 채널 해제
- `!readchannel` : 현재 자동 읽기 채널 확인
- `!settings` : 현재 서버 설정 확인
- `!autojoin <on|off>` : 자동 읽기 채널에 메시지가 오면 봇 자동 입장 여부 설정
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

## 티토커 느낌으로 맞춘 기본 사용 흐름

```text
!join
!setup
!female
!autojoin on
!xsaid off
!multilang on
!settings
```

## 한국어 / 영어 자동 읽기

- `multilang`가 켜져 있으면 메시지 내용을 보고 한국어/영어를 자동 판별해 읽어.
- 한국어가 포함되면 한국어 보이스를 우선 사용해.
- 영어만 있으면 영어 보이스를 사용해.
- 기본 매핑:
  - 한국어: `ko_female_1` -> `ko-KR-SunHiNeural`
  - 영어: `en_female_1` -> `en-US-JennyNeural`

예시:

```text
안녕하세요 반가워요
Hello, nice to meet you
```

## 자동 읽기 방식

1. 봇을 음성 채널에 먼저 입장시킴: `!join`
2. 읽고 싶은 텍스트 채널에서 `!setup`
3. 그 채널에 올라오는 일반 메시지를 자동으로 음성으로 읽음

- 명령어 메시지(`!`)는 자동 읽기에서 제외됨
- 봇 메시지는 읽지 않음
- 서버마다 설정이 따로 저장됨
- `autojoin`이 켜져 있으면, 봇이 음성 채널에 없을 때 메시지 작성자가 들어가 있는 음성 채널로 자동 입장 시도함
- `xsaid`가 켜져 있으면 `닉네임 + 메시지` 형식으로 읽고, 꺼져 있으면 메시지만 읽음

## 엔진 / 보이스 설정

현재 기본 탑재 엔진:
- `edge` : Microsoft Edge TTS

기본 보이스 별칭:
- `ko_female_1` -> `ko-KR-SunHiNeural`
- `ko_female_2` -> `ko-KR-JiMinNeural`
- `ko_male_1` -> `ko-KR-InJoonNeural`
- `ko_male_2` -> `ko-KR-BongJinNeural`
- `en_female_1` -> `en-US-JennyNeural`
- `en_male_1` -> `en-US-GuyNeural`

예시:

```text
!engines
!voices
!setengine edge
!setvoice ko_male_1
!male
!female
!voice
!sample en_female_1 Hello, this is a sample voice.
```

## 설정 파일

서버별 설정은 아래 파일에 저장돼:

```text
data/guild_settings.json
```

예를 들면 다음 정보가 들어가:
- 자동 읽기 채널 ID
- TTS 엔진
- voice_id
- autojoin
- xsaid
- multilang

## 목소리 샘플 파일

샘플 보관 폴더:

```text
voice_samples/
```

샘플 파일 생성:

```bash
python scripts/generate_voice_samples.py
```

## 설치

```bash
pip install -r requirements.txt
```

`.env.example`을 복사해서 `.env`를 만들고 값을 넣어.

```env
DISCORD_TOKEN=your-real-token
COMMAND_PREFIX=!
TTS_ENGINE=edge
TTS_VOICE=ko-KR-SunHiNeural
FFMPEG_PATH=ffmpeg
MAX_TTS_LENGTH=300
TTS_DATA_DIR=data
TTS_SAMPLES_DIR=voice_samples
```

## 실행

```bash
python main.py
```

## 필수 준비물

### 1) Discord bot 설정

- Discord Developer Portal에서 봇 생성
- Bot Token 발급
- Message Content Intent 활성화
- Voice 권한이 있는 상태로 서버에 초대

### 2) FFmpeg 설치

Windows라면 FFmpeg를 설치하고 PATH에 잡아 두는 게 제일 편해.

확인:

```bash
ffmpeg -version
```

PATH에 안 잡을 거면 `.env`에서 직접 지정해도 돼.

```env
FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe
```
