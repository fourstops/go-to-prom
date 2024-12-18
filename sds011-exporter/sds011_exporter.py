#!/usr/bin/python3

import os
import argparse
import time
import logging
from prometheus_client import start_http_server, Gauge
from sds011 import SDS011

# Logging Configuration
logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("/home/pi/sds011_exporter.log"),
        logging.StreamHandler()
    ],
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.info("""sds011_exporter.py - Expose readings from the SDS011 Particulate Sensor in Prometheus format
Press Ctrl+C to exit!
""")

def parse_args():
    parser = argparse.ArgumentParser(description="Measure air quality using an SDS011 sensor.")
    parser.add_argument("-b", "--bind", metavar="ADDRESS", default="0.0.0.0", help="Specify alternate bind address [default: 0.0.0.0]")
    parser.add_argument("-p", "--port", metavar="PORT", default=8001, type=int, help="Specify alternate port [default: 8001]")
    parser.add_argument("--delay", "-d", default=15, metavar="SECONDS", type=int, help="Seconds to pause after getting data before taking another measure (default: 15)")
    parser.add_argument("--measures", "-m", default=3, metavar="N", type=int, help="Get PM2.5 and PM10 values by taking N consecutive measures (default: 3)")
    parser.add_argument("--sensor", "-s", default="/dev/ttyUSB0", metavar="FILE", help="Path to the SDS011 sensor (default: '/dev/ttyUSB0')")
    return parser.parse_args()

# Prometheus metrics
PM25 = Gauge("PM25", "Particulate Matter of diameter less than 2.5 microns (µg/m³)")
PM10 = Gauge("PM10", "Particulate Matter of diameter less than 10 microns (µg/m³)")
AQI = Gauge("AQI", "Air Quality Index based on PM2.5 levels")

# AQI Breakpoints for PM2.5 (US EPA standard)
AQI_BREAKPOINTS_PM25 = [
    (0.0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 350.4, 301, 400),
    (350.5, 500.4, 401, 500),
]

def calculate_aqi(pm25):
    """Calculate AQI for PM2.5 using US EPA breakpoints."""
    for low, high, aqi_low, aqi_high in AQI_BREAKPOINTS_PM25:
        if low <= pm25 <= high:
            aqi = ((aqi_high - aqi_low) / (high - low)) * (pm25 - low) + aqi_low
            return round(aqi)
    return -1  # Invalid AQI if PM2.5 is out of range

def read_sensor(sensor, measures, delay):
    """Read PM2.5 and PM10 data from the SDS011 sensor."""
    sensor.sleep(sleep=False)
    time.sleep(10)

    pm25, pm10 = 0.0, 0.0
    for _ in range(measures):
        values = sensor.query()
        pm25 += values[0]
        pm10 += values[1]
        time.sleep(delay)

    sensor.sleep(sleep=True)
    return round(pm25 / measures, 1), round(pm10 / measures, 1)

def main():
    args = parse_args()
    sensor = SDS011(args.sensor)

    start_http_server(args.port)
    logging.info(f"Prometheus metrics server started on {args.bind}:{args.port}")

    while True:
        pm25, pm10 = read_sensor(sensor, args.measures, args.delay)
        aqi = calculate_aqi(pm25)

        PM25.set(pm25)
        PM10.set(pm10)
        AQI.set(aqi)

        logging.info(f"PM2.5: {pm25} µg/m³, PM10: {pm10} µg/m³, AQI: {aqi}")
        time.sleep(args.delay)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully...")
