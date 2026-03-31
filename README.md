# Discord TTS Bot

디스코드 음성 채널에서 실제로 쓸 수 있는 수준의 TTS 봇이야.

## 기능

- `!join` : 명령을 보낸 사용자가 있는 음성 채널에 입장
- `!leave` : 음성 채널에서 퇴장하고 대기열 정리
- `!say <문장>` : 직접 TTS 재생
- `!setreadchannel [#채널]` : 자동 읽기 채널 지정
- `!clearreadchannel` : 자동 읽기 채널 해제
- `!readchannel` : 현재 자동 읽기 채널 확인
- `!engines` : 사용 가능한 TTS 엔진 목록 확인
- `!voices [engine]` : 사용 가능한 보이스 목록 확인
- `!setengine <engine>` : TTS 엔진 변경
- `!setvoice <voice_id>` : 보이스 변경
- `!voice` : 현재 엔진/보이스 확인
- `!sample [voice_id] [문장]` : 샘플 보이스 재생
- `!skip` : 현재 재생 중인 음성 스킵
- `!stop` : 현재 재생 중인 음성 정지 + 대기열 비우기
- `!queue` : 현재 재생/대기 상태 확인
- `!ping` : 상태 확인

## 자동 읽기 방식

1. 봇을 음성 채널에 먼저 입장시킴: `!join`
2. 읽고 싶은 텍스트 채널에서 `!setreadchannel`
3. 그 채널에 올라오는 일반 메시지를 자동으로 음성으로 읽음

- 명령어 메시지(`!`)는 자동 읽기에서 제외됨
- 봇 메시지는 읽지 않음
- 서버마다 설정이 따로 저장됨

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
!voice
!sample ko_female_2 안녕하세요 샘플입니다
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

## 목소리 샘플 파일

샘플 보관 폴더:

```text
voice_samples/
```

샘플 파일 생성:

```bash
python scripts/generate_voice_samples.py
```

생성 예시:
- `voice_samples/ko_female_1.mp3`
- `voice_samples/ko_female_2.mp3`
- `voice_samples/ko_male_1.mp3`
- `voice_samples/ko_male_2.mp3`

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

## 추천 테스트 순서

1. 봇 실행
2. 디스코드 음성 채널 입장
3. `!join`
4. 텍스트 채널에서 `!setreadchannel`
5. 일반 채팅을 보내서 자동 읽기 확인
6. `!setvoice ko_female_2` 같은 식으로 보이스 변경
7. `!sample`로 샘플 재생 확인
8. `!queue`, `!skip`, `!stop` 확인

## 한계

- 현재는 prefix 명령어 기반이고 슬래시 커맨드는 아님
- 엔진은 구조상 분리돼 있지만 실제 구현은 현재 `edge`만 들어 있음
- 첨부파일/임베드/이모지 같은 복잡한 메시지는 아직 텍스트 정제 로직이 단순함

## 다음에 붙이기 좋은 것들

- 슬래시 커맨드 전환
- 특정 역할만 설정 변경 가능하게 강화
- 금칙어/링크 필터링
- 사용자별 음성 설정
- 관리자 웹 패널
- ElevenLabs / OpenAI TTS 연동
