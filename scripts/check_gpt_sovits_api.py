from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser(description="Check GPT-SoVITS API availability")
    parser.add_argument("--url", default="http://127.0.0.1:9880/tts")
    parser.add_argument("--method", default="GET", choices=["GET", "POST"])
    parser.add_argument("--voice-ref", default=None, help="optional ref.wav path for POST test")
    parser.add_argument("--prompt-text", default="안녕하세요. 저는 테스트용 샘플 화자입니다.")
    parser.add_argument("--text", default="안녕하세요. GPT-SoVITS 연결 테스트입니다.")
    args = parser.parse_args()

    data = None
    headers = {}
    if args.method == "POST":
        payload = {
            "text": args.text,
            "text_lang": "ko",
            "prompt_lang": "ko",
            "prompt_text": args.prompt_text,
        }
        if args.voice_ref:
            payload["ref_audio_path"] = args.voice_ref
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(args.url, data=data, headers=headers, method=args.method)

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read(400)
            print(f"[OK] status={response.status}")
            print(f"[OK] content-type={response.headers.get('Content-Type', '')}")
            if body:
                try:
                    print(body.decode("utf-8", errors="ignore"))
                except Exception:
                    print("[INFO] binary body returned")
            return 0
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        print(f"[HTTP_ERROR] status={exc.code}")
        if detail:
            print(detail)
        return 1
    except urllib.error.URLError as exc:
        print(f"[CONNECTION_ERROR] {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
