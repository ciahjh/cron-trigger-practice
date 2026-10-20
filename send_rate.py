import json
import os
import urllib.request

BASE = os.environ.get("BASE_CURRENCY", "USD")
TARGET = os.environ.get("TARGET_CURRENCY", "KRW")
BOT_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def fetch_rate(base, target):
    url = f"https://open.er-api.com/v6/latest/{base}"
    with urllib.request.urlopen(url, timeout=10) as res:
        data = json.load(res)
    if data.get("result") != "success":
        raise RuntimeError(f"환율 조회 실패: {data}")
    return data["rates"][target]


WEATHER_CODES = {
    0: "맑음", 1: "대체로 맑음", 2: "구름 조금", 3: "흐림",
    45: "안개", 48: "안개", 51: "이슬비", 53: "이슬비", 55: "이슬비",
    61: "비", 63: "비", 65: "강한 비", 71: "눈", 73: "눈", 75: "강한 눈",
    80: "소나기", 81: "소나기", 82: "강한 소나기", 95: "뇌우",
}


def fetch_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=36.3504&longitude=127.3845"
        "&current=temperature_2m,weather_code"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        "&timezone=Asia%2FSeoul&forecast_days=1"
    )
    with urllib.request.urlopen(url, timeout=10) as res:
        data = json.load(res)
    cur, day = data["current"], data["daily"]
    desc = WEATHER_CODES.get(cur["weather_code"], "알 수 없음")
    return (
        f"{desc} {cur['temperature_2m']:.0f}°C "
        f"(최저 {day['temperature_2m_min'][0]:.0f}° / 최고 {day['temperature_2m_max'][0]:.0f}°, "
        f"강수확률 {day['precipitation_probability_max'][0]}%)"
    )


def send_message(text):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=json.dumps({"chat_id": CHAT_ID, "text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=10).read()


def main():
    rate = fetch_rate(BASE, TARGET)
    weather = fetch_weather()
    send_message(
        f"💱 오늘의 환율: 1 {BASE} = {rate:,.2f} {TARGET}\n"
        f"🌤 대전 날씨: {weather}"
    )


if __name__ == "__main__":
    main()
