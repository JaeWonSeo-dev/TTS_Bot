# Discord TTS Bot

간단한 디스코드 TTS 봇 스캐폴드야.

## 기능

- `!join` : 명령을 보낸 사용자가 있는 음성 채널에 입장
- `!leave` : 음성 채널에서 퇴장
- `!say <문장>` : 입력한 문장을 TTS로 생성해서 음성 채널에서 재생
- `!ping` : 상태 확인

## 파일

- `main.py` : 봇 실행 파일
- `requirements.txt` : 필요한 파이썬 패키지
- `.env.example` : 환경 변수 예시

## 설치

```bash
pip install -r requirements.txt
```

`.env.example`을 복사해서 `.env`를 만들고 토큰을 넣어.

```env
DISCORD_TOKEN=your-real-token
COMMAND_PREFIX=!
TTS_LANGUAGE=ko
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
- 봇을 서버에 초대

### 2) FFmpeg 설치

`discord.py`가 음성 재생할 때 FFmpeg가 필요해.

Windows라면:
- FFmpeg 설치
- `ffmpeg`가 PATH에 잡혀 있어야 함

확인:

```bash
ffmpeg -version
```

## 주의

- 현재는 `gTTS` 기반이라 Google TTS를 사용함
- 같은 시점에 여러 `!say` 요청이 오면 마지막 요청이 이전 재생을 끊고 재생함
- 파일 기반 임시 mp3를 생성해서 재생함

## 다음에 붙이기 좋은 것들

- 재생 대기열(queue)
- 사용자별 음성/속도 설정
- 슬래시 커맨드 전환
- ElevenLabs / Azure / OpenAI TTS 연동
- 텍스트 채널 메시지 자동 읽기
