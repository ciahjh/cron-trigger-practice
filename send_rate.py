import datetime
import json
import os
import urllib.parse
import urllib.request

API_URL = "https://api.frankfurter.dev/v2/rates"
METAL_URL = "https://api.gold-api.com/price"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
HEADERS = {"User-Agent": "send-rate/1.0"}
G_PER_OZ = 31.1034768
OZ_PER_KG = 1000 / G_PER_OZ
LB_PER_KG = 1 / 0.45359237
WEEKDAYS = "월화수목금토일"

# 강수 알림 대상 도시 (이름, 위도, 경도)
CITIES = [("대전", 36.3504, 127.3845)]
RAIN_THRESHOLD = 50


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.load(res)


def fetch_krw_rate(base):
    query = urllib.parse.urlencode({"base": base, "quotes": "KRW"})
    data = get_json(f"{API_URL}?{query}")[0]
    return data["rate"], data["date"]


def fetch_usd_price(symbol):
    return get_json(f"{METAL_URL}/{symbol}")["price"]


def fetch_rain_probabilities(cities):
    """예보 날짜(YYYY-MM-DD)와 도시별 오늘의 최대 강수확률(%)을 반환한다."""
    query = urllib.parse.urlencode(
        {
            "latitude": ",".join(str(lat) for _, lat, _ in cities),
            "longitude": ",".join(str(lon) for _, _, lon in cities),
            "daily": "precipitation_probability_max",
            "timezone": "Asia/Seoul",
            "forecast_days": 1,
        }
    )
    data = get_json(f"{WEATHER_URL}?{query}")
    # 위치가 여러 개면 위치별 결과의 배열로 응답한다.
    if isinstance(data, dict):
        data = [data]
    date = data[0]["daily"]["time"][0]
    probs = [
        (name, item["daily"]["precipitation_probability_max"][0])
        for (name, _, _), item in zip(cities, data)
    ]
    return date, probs


def format_date(date):
    day = datetime.date.fromisoformat(date)
    return f"{date} ({WEEKDAYS[day.weekday()]})"


def send_telegram(token, chat_id, text):
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(url, data=body, timeout=10) as res:
        res.read()


def build_rate_text():
    usd, date = fetch_krw_rate("USD")
    eur, _ = fetch_krw_rate("EUR")
    jpy, _ = fetch_krw_rate("JPY")

    gold = fetch_usd_price("XAU")
    silver = fetch_usd_price("XAG")
    copper = fetch_usd_price("HG")

    return (
        f"환율 - {format_date(date)} 기준\n"
        f"USD 1달러: {usd:,.2f}원\n"
        f"EUR 1유로: {eur:,.2f}원\n"
        f"JPY 100엔: {jpy * 100:,.2f}원\n"
        f"\n"
        f"원자재 (USD / 원화)\n"
        f"금: ${gold:,.2f}/oz ({gold / G_PER_OZ * usd:,.0f}원/g)\n"
        f"은: ${silver:,.2f}/oz ({silver * OZ_PER_KG * usd:,.0f}원/kg)\n"
        f"구리: ${copper:,.4f}/lb ({copper * LB_PER_KG * usd:,.0f}원/kg)"
    )


def build_rain_text(threshold):
    """강수확률이 threshold% 이상인 도시를 알리고, 없으면 비 소식이 없다고 알린다."""
    date, probs = fetch_rain_probabilities(CITIES)
    rainy = [
        (name, prob) for name, prob in probs if prob is not None and prob >= threshold
    ]
    title = f"강수 알림 - {format_date(date)}"
    if not rainy:
        return f"{title}\n오늘은 강수확률 {threshold}% 이상인 도시가 없습니다. 비 소식 없음"
    rainy.sort(key=lambda item: item[1], reverse=True)
    lines = [title, f"강수확률 {threshold}% 이상인 도시"]
    lines += [f"{name}: {prob}%" for name, prob in rainy]
    return "\n".join(lines)


def main():
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    text = build_rate_text() + "\n\n" + build_rain_text(RAIN_THRESHOLD)
    send_telegram(token, chat_id, text)
    print(text)


if __name__ == "__main__":
    main()
