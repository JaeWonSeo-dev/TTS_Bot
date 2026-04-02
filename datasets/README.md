# Datasets

이 폴더는 B 방식 학습용 화자 데이터셋을 보관한다.

## 구조

```text
datasets/
  <voice_id>/
    wavs/
      0001.wav
      0002.wav
    metadata.csv
    speaker.json
```

## 필수 파일

- `wavs/*.wav`: 화자 음성 조각
- `metadata.csv`: `파일명|문장` 형식

## 선택 파일

- `speaker.json`: 표시 이름, 언어, 설명 등 메타 정보

## 권장 규칙

- 파일명은 `0001.wav` 같은 순차 번호 권장
- 문장은 실제 발화와 최대한 일치해야 함
- 한 폴더에는 한 사람 데이터만 넣기
