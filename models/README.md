# Models

공통 베이스 모델, 학습 설정 파일, 체크포인트 경로를 여기에 둔다.

예시:

```text
models/
  xtts_v2/
    model.pth
    config.json
  xtts_finetune_config.json
```

현재 `training/train_voice.py`는 기본적으로 아래 경로를 기대한다:

- `models/xtts_v2/model.pth`
- `models/xtts_finetune_config.json`

환경에 따라 실제 경로는 바꿔도 된다.
