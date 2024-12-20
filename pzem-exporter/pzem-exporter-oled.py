import os
import time
import logging
import argparse

from pzem import PZEM_016
from prometheus_client import start_http_server, Gauge
from PIL import Image, ImageDraw, ImageFont
import board
from adafruit_ssd1306 import SSD1306_I2C

# Logging setup
logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("pzem_exporter.log"),
              logging.StreamHandler()],
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Prometheus Gauges
VOLTAGE = Gauge('voltage', 'Voltage measured (V)')
CURRENT = Gauge('current', 'Current measured in amps (A)')
WATTS = Gauge('watts', 'Power consumption measured (W)')
ENERGY = Gauge('energy', 'Energy measured (W-hr)')
FREQUENCY = Gauge('frequency', 'AC frequency measured (Hz)')
POWER_FACTOR = Gauge('power_factor', 'Power efficiency (%)')
ALARM = Gauge('alarm', 'Alarm status (boolean)')

# Initialize PZEM
pzem = PZEM_016("/dev/ttyUSB0")  # Replace with the correct path

# OLED setup
i2c = board.I2C()
oled = SSD1306_I2C(128, 64, i2c)

# Create blank image for drawing
image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)

# Load font with size 10
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font = ImageFont.truetype(font_path, 10)

# Clear display at startup
oled.fill(0)
oled.show()

def get_readings():
    for attempt in range(3):  # Retry up to 3 times
        try:
            reading = pzem.read()
            logging.info(f"Reading successful on attempt {attempt + 1}: {reading}")
            VOLTAGE.set(reading["voltage"])
            CURRENT.set(reading["current"])
            WATTS.set(reading["power"])
            ENERGY.set(reading["energy"])
            FREQUENCY.set(reading["frequency"])
            POWER_FACTOR.set(reading["power_factor"])
            ALARM.set(reading["alarm_status"])
            return reading
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(1)
    logging.error("Failed to get readings after 3 attempts.")
    return None

def update_oled_display(reading):
    try:
        # Clear the image
        draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)

        # Draw text on the image with updated spacing
        draw.text((0, 2), f"Voltage: {reading['voltage']} V", font=font, fill=255)
        draw.text((0, 12), f"Current: {reading['current']} A", font=font, fill=255)
        draw.text((0, 22), f"Power: {reading['power']} W", font=font, fill=255)
        draw.text((0, 32), f"Energy: {reading['energy']} Wh", font=font, fill=255)
        draw.text((0, 42), f"Freq: {reading['frequency']} Hz", font=font, fill=255)
        draw.text((0, 52), f"PF: {reading['power_factor']}", font=font, fill=255)

        # Display the image
        oled.image(image)
        oled.show()
    except Exception as e:
        logging.error(f"Failed to update OLED display: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bind", default='0.0.0.0', help="Bind address")
    parser.add_argument("-p", "--port", default=8002, type=int, help="HTTP server port")
    parser.add_argument("--delay", default=10, type=int, help="Delay between readings in seconds")
    args = parser.parse_args()

    logging.info(f"Starting HTTP server on {args.bind}:{args.port}")
    start_http_server(addr=args.bind, port=args.port)

    try:
        while True:
            try:
                reading = get_readings()
                if reading:
                    update_oled_display(reading)
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
            time.sleep(args.delay)
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully.")
        oled.fill(0)
        oled.show()
        exit(0)

if __name__ == "__main__":
    main()
