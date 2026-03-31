# Discord TTS Bot

디스코드 음성 채널에서 실제로 쓸 수 있는 수준의 TTS 봇이야.

## 기능

- `!join` : 명령을 보낸 사용자가 있는 음성 채널에 입장
- `!leave` : 음성 채널에서 퇴장하고 대기열 정리
- `!say <문장>` : TTS 생성 후 대기열에 추가
- `!skip` : 현재 재생 중인 음성 스킵
- `!stop` : 현재 재생 중인 음성 정지 + 대기열 비우기
- `!queue` : 현재 재생/대기 상태 확인
- `!ping` : 상태 확인

## 개선된 점

- `edge-tts` 기반으로 더 자연스러운 한국어 음성 사용
- 요청이 여러 개 와도 대기열(queue)로 순서대로 재생
- 임시 mp3 파일을 요청마다 따로 생성
- 재생 후 임시 파일 자동 삭제
- 서버별(guild별)로 재생 상태 분리
- 봇이 이미 다른 음성 채널에 있으면 이동 처리

## 파일

- `main.py` : 봇 실행 파일
- `requirements.txt` : 필요한 파이썬 패키지
- `.env.example` : 환경 변수 예시

## 설치

```bash
pip install -r requirements.txt
```

`.env.example`을 복사해서 `.env`를 만들고 값을 넣어.

```env
DISCORD_TOKEN=your-real-token
COMMAND_PREFIX=!
TTS_VOICE=ko-KR-SunHiNeural
FFMPEG_PATH=ffmpeg
MAX_TTS_LENGTH=300
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
4. `!say 안녕하세요 테스트입니다`
5. 여러 번 `!say`를 보내서 대기열 동작 확인
6. `!queue`, `!skip`, `!stop` 확인

## 한계

- 현재는 prefix 명령어 기반이고 슬래시 커맨드는 아님
- 텍스트 채널 메시지 자동 읽기는 아직 없음
- 고급 권한 제어(특정 역할만 사용 가능)는 아직 없음

## 다음에 붙이기 좋은 것들

- 슬래시 커맨드 전환
- 특정 텍스트 채널 자동 읽기
- 금칙어/링크 필터링
- 사용자별 음성 설정
- 관리용 설정 파일(JSON/YAML)
- ElevenLabs / OpenAI TTS 연동
