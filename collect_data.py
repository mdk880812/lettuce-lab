import os
import time
import hmac
import hashlib
import base64
import uuid
import csv
from datetime import datetime, timezone, timedelta
import requests

TOKEN = os.environ["SWITCHBOT_TOKEN"]
SECRET = os.environ["SWITCHBOT_SECRET"]

def get_headers():
    nonce = str(uuid.uuid4())
    t = int(round(time.time() * 1000))
    string_to_sign = f"{TOKEN}{t}{nonce}".encode("utf-8")
    sign = base64.b64encode(
        hmac.new(SECRET.encode("utf-8"), msg=string_to_sign, digestmod=hashlib.sha256).digest()
    ).decode("utf-8")
    return {
        "Authorization": TOKEN,
        "Content-Type": "application/json",
        "charset": "utf8",
        "t": str(t),
        "sign": sign,
        "nonce": nonce,
    }

def main():
    headers = get_headers()
    res = requests.get("https://switch-bot.com", headers=headers).json()
    devices = res.get("body", {}).get("deviceList", [])

    temp, humidity, co2, power_w, plug_state = None, None, None, None, None

    for dev in devices:
        dev_id = dev["deviceId"]
        dev_type = dev.get("deviceType", "")
        status = requests.get(f"https://switch-bot.com/{dev_id}/status", headers=headers).json().get("body", {})

        if "CO2" in dev_type or "Meter" in dev_type:
            temp = status.get("temperature")
            humidity = status.get("humidity")
            co2 = status.get("CO2")
        elif "Plug" in dev_type:
            power_w = status.get("weight")
            plug_state = status.get("power")

    jst = timezone(timedelta(hours=9))
    now_str = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

    file_path = "farm_data.csv"
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp_jst", "temperature_c", "humidity_pct", "co2_ppm", "plug_state", "power_w"])
        writer.writerow([now_str, temp, humidity, co2, plug_state, power_w])

    print(f"[{now_str}] 저장 완료 -> 온도:{temp}°C, 습도:{humidity}%, CO2:{co2}ppm, 플러그:{plug_state}({power_w}W)")

if __name__ == "__main__":
    main()
