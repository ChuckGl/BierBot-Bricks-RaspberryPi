import json
import logging
import time

import requests
import RPi.GPIO as GPIO
import yaml  # reading the config
from w1thermsensor import W1ThermSensor

try:
    import httplib  # python < 3.0
except Exception:
    import http.client as httplib

from yaml.loader import SafeLoader

logging.basicConfig(
    filename="./bricks.log",
    filemode="w+",
    level=logging.INFO,
    format="%(asctime)s;%(levelname)s;%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger().addHandler(logging.StreamHandler())

APIKEY = "tbd"
TYPE = "RaspberryPi"
CHIPID = "tbd"
NEXT_REQUEST_MS_FALLBACK = 60000

# Open the file and load the file
config = {}  # will hold the config from bricks.yaml and cache local relay states
with open("./bricks.yaml") as f:
    config = yaml.load(f, Loader=SafeLoader)
    logging.info("read config")

    APIKEY = config["apikey"]
    CHIPID = config["device_id"]
    TYPE = config["meta"]["platform"]

    logging.info(f"apikey={APIKEY}, device_id={CHIPID}, platform={TYPE}")

last_temps = {}

GPIO.setwarnings(False)


def initRelays() -> None:
    logging.info("setting GPIO to GPIO.BOARD")
    GPIO.setmode(GPIO.BOARD)

    for i in range(0, len(config["relays"])):
        config["relays"][i]["state"] = 0
        gpio_number = config["relays"][i]["gpio"]
        logging.info(f"initializing relay {i+1} (GPIO {gpio_number})...")
        GPIO.setup(gpio_number, GPIO.OUT)
        GPIO.output(gpio_number, 0)


def setRelay(number: int = 0, state: int = 0) -> None:
    # number relay number in config
    # state: 0=off, 1=on
    config["relays"][number]["state"] = state
    gpio_number = config["relays"][number]["gpio"]
    logging.info(f"setting relay {number+1} (GPIO {gpio_number}) to {state}...")
    corrected_state = -1
    invert = config["relays"][number]["invert"]
    if invert:
        if state == 0:
            corrected_state = 1
        else:
            corrected_state = 0

        logging.info(f"inverted {state} to {corrected_state}")
    else:
        corrected_state = state

    GPIO.output(gpio_number, corrected_state)


def getRelay(number: int = 0) -> int:
    return config["relays"][number]["state"]  # TODO: get from GPIO?


def haveInternet() -> bool:
    # from https://stackoverflow.com/questions/3764291
    conn = httplib.HTTPSConnection("8.8.8.8", timeout=5)
    try:
        conn.request("HEAD", "/")
        return True
    except Exception:
        return False
    finally:
        conn.close()


def request() -> None:
    logging.info("starting request")
    url = "https://brewbricks.com/api/iot/v1"

    # craft request
    post_fields = {
        "type": TYPE,
        "brand": "oss",
        "version": "0.2",
        "chipid": CHIPID,
        "apikey": APIKEY,
    }  # baseline
    # add relay states to request
    for i in range(0, len(config["relays"])):
        key = f"a_bool_epower_{i}"
        value = getRelay(i)
        post_fields[key] = str(value)
        logging.info(f"set relay {i+1} to {value}")

    # add temperatures to request
    for i, sensor_id in enumerate(config["temperature_sensors"]):
        key = f"s_number_temp_{i}"
        try:
            sensor = W1ThermSensor(sensor_id=sensor_id)
            temperature = sensor.get_temperature()
            last_temps[sensor_id] = temperature
        except Exception:
            logging.error("sensor was not ready, using last temp")
            if sensor_id in last_temps:
                temperature = last_temps[sensor_id]
            else:
                temperature = -42
        value = temperature
        post_fields[key] = str(value)
        logging.info(f"set tempsensor {i+1} with id {sensor_id} to {temperature}")

    response = requests.get(url, params=post_fields)

    try:
        next_request_ms = NEXT_REQUEST_MS_FALLBACK
        if response.text == "internal.":
            logging.info("please activate RasberryPi under https://bricks.bierbot.com > Bricks")
            time.sleep(next_request_ms / 1000)
        else:
            json_response = json.loads(response.text)

            next_request_ms = json_response["next_request_ms"]

            # set relays based on response
            for i in range(0, len(config["relays"])):
                relay_key = f"epower_{i}_state"
                if relay_key in json_response:
                    # relay_key is e.g. "epower_0_state"
                    new_relay_state = int(json_response[relay_key])
                    logging.info(f"received new target state {new_relay_state} for relay {i+1}")
                    setRelay(i, new_relay_state)
                else:
                    logging.warning(
                        f"relay key {relay_key} for relay {i+1} was expected but not in response. "
                        "This is normal before activation."
                    )
                    setRelay(i, 0)

            logging.info(f"sleeping for {next_request_ms}ms")
            time.sleep(next_request_ms / 1000)
    except Exception:
        logging.warning("failed processing request: " + response.text)
        time.sleep(60)


def run() -> None:
    initRelays()

    logging.info("checking for internet connection...")
    while not haveInternet():
        logging.info("No internet - sleeping for 1s.")
        time.sleep(1)

    while True:
        request()


if __name__ == "__main__":
    logging.info("BierBot Bricks RaspberryPi client started.")
    run()
