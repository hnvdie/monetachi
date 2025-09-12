from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from modules.blockchain import read_tron as tronscan

import socket
import board
import busio
import adafruit_ssd1306
import requests
import time
import toml

config = toml.load("config.toml")
currency_symbols = {"usd":"$","idr":"Rp","jpy":"¥","eur":"€"}

def token_value(token_id, amount, target_currency="usd"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies={target_currency}"
    try:
        response = requests.get(url, timeout=5).json()
        price = response[token_id][target_currency.lower()]
    except:
        price = 0
    total_value = amount * price
    symbol = currency_symbols.get(target_currency.lower(), "")
    total_value_fmt = f"{symbol}{total_value:,.0f}"

    # custom token name
    if token_id.lower() == "shiba-inu":
        token_id = "shiba"
    if token_id.lower() == "dogecoin":
        token_id = "doge"

    return token_id.capitalize(), total_value, total_value_fmt


def wallet_info(default_currency="jpy"):
    tokens = list(config["walletOffline"].items())
    def merge_tokens(tokens):
        merged = {}
        for name, balance in tokens:
            merged[name] = merged.get(name, 0) + balance
        return list(merged.items())

    # bad logic need someone for improve code here
    if config["wallet"]:
       for data in config["wallet"]:
           chain = data["chain"]

           if chain.lower() == "tron":
              for _ in tronscan(data["addr"]):
                 tokens.append((
			_["name"],
			int(_["balance"])),
			)

           elif chain.lower() == "solana":
              # underconstruction
              pass
           else:pass

    tokens = merge_tokens(tokens)
    lines = []
    total = 0
    for token_id, amount in tokens:
        name, value, value_fmt = token_value(token_id, amount, default_currency)
        lines.append(f"{name}: {value_fmt}")
        total += value

    symbol = currency_symbols.get(default_currency.lower(), "")
    lines.append(f"Net: {symbol}{total:,.0f}")
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

print(wallet_info())

i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
oled.fill(0)
oled.show()
font_path = "fonts/ubuntu.ttf"

last_fetch = 0
wallet_lines = []

while True:
    if time.time() - last_fetch > 3600:
        wallet_lines = wallet_info()
        last_fetch = time.time()

    ip = get_ip()
    messages = [f"Host: {ip}"] + wallet_lines

    for msg in messages:
        font_size = 13
        font = ImageFont.truetype(font_path, font_size)
        w, h = font.getsize(msg)
        while w > oled.width - 4 and font_size > 6:  # padding 2px
            font_size -= 1
            font = ImageFont.truetype(font_path, font_size)
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
