import os
import time
import logging
import argparse
import json

from pzem import PZEM_016
from prometheus_client import start_http_server, Gauge

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
pzem = PZEM_016("/dev/ttyUSB0")  # Update the device path if necessary

# Collect sensor data with retries and sleep between attempts
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
            time.sleep(1)  # Small delay before retrying
    logging.error("Failed to get readings after 3 attempts.")
    return None

# Main function
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
                get_readings()
            except Exception as e:
                logging.error(f"Error in main loop: {e}")

            # Sleep between loop iterations
            time.sleep(args.delay)
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully.")
        exit(0)

if __name__ == "__main__":
    main()
