# Monetachi ¥

from datetime import datetime

import socket
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import requests
import time

currency_symbols = {"usd":"$","idr":"Rp","jpy":"¥","eur":"€"}

def token_value(token_id, amount, currency="usd"):
    symbol = currency_symbols.get(currency.lower(), "")
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies={currency}"
    try:
        response = requests.get(url, timeout=5).json()
        price = response[token_id][currency.lower()]
    except:
        price = 0
    total_value = amount * price
    total_value_fmt = f"{symbol}{total_value:,.0f}"
    #custom display token name
    if token_id.upper() == "SHIBA-INU":
       token_id = "shiba"

    return f"{token_id.capitalize()} value: {total_value_fmt}"

def wallet_info(default_currency="jpy"):
    tokens = [
        ("shiba-inu", 50_50_50.4, "jpy"),
        ("doge", 55, "jpy"),
        ("bitcoin", 0.03, "jpy")
    ]

    lines = []
    total = 0
    for token_id, amount, currency in tokens:
        line = token_value(token_id, amount, currency)
        lines.append(line)
        symbol = currency_symbols.get(currency.lower(), "")
        # ambil numeric value dari string
        value_str = line.split(symbol)[1].replace(",","")
        try:
            total += float(value_str)
        except:
            pass

    symbol = currency_symbols.get(default_currency.lower(), "")
    lines.append(f"Networth: {symbol}{total:,.0f}")
    return lines

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "No IP"
    finally:
        s.close()
    return ip

i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
oled.fill(0)
oled.show()
font = ImageFont.truetype("ubuntu.ttf", 13)

last_fetch = 0
wallet_lines = []

while True:
    # set update data here, like 1H, 30m, etc.
    if time.time() - last_fetch > 3600:
        wallet_lines = wallet_info()
        last_fetch = time.time()

    ip = get_ip()
    messages = [f"Host: {ip}"] + wallet_lines

    for msg in messages:
        w, h = font.getsize(msg)
        x = (oled.width - w) // 2
        y = (oled.height - h) // 2

        for brightness in list(range(0, 256, 25)) + list(range(255, -1, -25)):
            image = Image.new("1", (oled.width, oled.height))
            draw = ImageDraw.Draw(image)
            draw.text((x, y), msg, font=font, fill=brightness//128)
            oled.image(image)
            oled.show()
            time.sleep(0.02)
