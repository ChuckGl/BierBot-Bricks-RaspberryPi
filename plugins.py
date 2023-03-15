"""
Launch Pad to integrate other devices with the Raspberry Pi Brick.
    Devices Supported:
        1. TP-Link Kasa Devices using python-kasa

------------------------
"""

import sys
import os
import logging
import yaml
from yaml.loader import SafeLoader
from kasa import SmartPlug

class output():
    def __init__(self, gpio_number=0, state=0):
            self.gpio_number = gpio_number
            self.state = state
            logging.info(f"GPIO_NO= {gpio_number} STATE= {state}")
            # read the config again so we have it all here
            config = {} 
            with open('./bricks.yaml') as f:
                config = yaml.load(f, Loader=SafeLoader)
                logging.info("plugins read config")

            # Loop through the config and process any relay with a gpio over 200
            for i in range(0, len(config["relays"])):
                gpio_num = config["relays"] [i] ["gpio"]
                logging.info(f"GPIO_NUM= {gpio_num}")
                if gpio_num == gpio_number:
                    device = config["relays"] [i] ["device"]
                    logging.info(f"I = {i}")
                    logging.info(f"Device Type= {device}   State= {state}")

                    # Processing the device based on device name.  Add new plugins as elif statement after kasa.

                    # TP-Link Kasa SmartPlugs.      
                    if device == "kasa":
                        alias = config["relays"] [i] ["alias"]
                        logging.info(f"Alias= {alias}")
                        if state == 0:
                            os.system('kasa --alias "{0}" off'.format(alias))
                        else:
                            os.system('kasa --alias "{0}" on'.format(alias))
