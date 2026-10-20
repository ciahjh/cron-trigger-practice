import json
import os
import urllib.request

BASE = os.environ.get("BASE_CURRENCY", "USD")
TARGET = os.environ.get("TARGET_CURRENCY", "KRW")
WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]


def fetch_rate(base, target):
    url = f"https://open.er-api.com/v6/latest/{base}"
    with urllib.request.urlopen(url, timeout=10) as res:
        data = json.load(res)
    if data.get("result") != "success":
        raise RuntimeError(f"환율 조회 실패: {data}")
    return data["rates"][target]


def send_message(text):
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps({"text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=10).read()


def main():
    rate = fetch_rate(BASE, TARGET)
    send_message(f"💱 오늘의 환율: 1 {BASE} = {rate:,.2f} {TARGET}")


if __name__ == "__main__":
    main()
