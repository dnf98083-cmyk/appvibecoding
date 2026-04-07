import os
import time
import requests
from pathlib import Path

# .env 파일 수동 로드
env_path = Path(__file__).parent / ".env"
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()

API_KEY = os.environ.get("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

def test_text(prompt="안녕하세요! 한국어로 짧게 자기소개 해줘."):
    print("\n[텍스트 생성 테스트] qwen/qwen3-plus:free")
    print(f"  입력: {prompt}")
    payload = {
        "model": "qwen/qwen3.6-plus:free",
        "messages": [{"role": "user", "content": prompt}],
    }
    res = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=30)
    if not res.ok:
        print(f"  [HTTP {res.status_code}] {res.text}")
        res.raise_for_status()
    reply = res.json()["choices"][0]["message"]["content"]
    print(f"  응답: {reply}")
    return reply

def test_image():
    print("\n[이미지 인식 테스트] google/gemma-3-27b-it:free")
    # 간단한 1x1 빨간 픽셀 PNG (base64)
    red_pixel_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
        "z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
    )
    print("  입력: 1x1 빨간 픽셀 이미지")
    payload = {
        "model": "google/gemma-3-27b-it:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{red_pixel_b64}"
                        },
                    },
                    {"type": "text", "text": "이 이미지에 무엇이 보이나요? 한국어로 설명해 주세요."},
                ],
            }
        ],
    }
    res = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=30)
    if not res.ok:
        print(f"  [HTTP {res.status_code}] {res.text}")
        res.raise_for_status()
    reply = res.json()["choices"][0]["message"]["content"]
    print(f"  응답: {reply}")
    return reply

if __name__ == "__main__":
    print("=" * 50)
    print("  OpenRouter API 테스트")
    print("=" * 50)

    try:
        test_text()
    except Exception as e:
        print(f"  [오류] 텍스트 테스트 실패: {e}")

    print("\n  (3초 대기 중...)")
    time.sleep(3)

    try:
        test_image()
    except Exception as e:
        print(f"  [오류] 이미지 테스트 실패: {e}")

    print("\n" + "=" * 50)
    print("  테스트 완료")
    print("=" * 50)
