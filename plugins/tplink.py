import asyncio
import logging
import yaml
from yaml.loader import SafeLoader
from kasa import Discover, SmartPlug

class output():
    # Class-level variables to store device info and config
    device_info = {}
    config = {}

    def __init__(self, gpio_number=0, state=0):
        # Perform discovery only if device_info is empty
        if not output.device_info:
            output.device_info = asyncio.run(self.discover_devices())

        # Read config only if it's empty
        if not output.config:
            with open('./bricks.yaml') as f:
                output.config = yaml.load(f, Loader=SafeLoader)

        self.gpio_number = gpio_number
        self.state = state

        for relay in output.config["relays"]:
            if "device" not in relay or "alias" not in relay or not relay["device"] or not relay["alias"]:
                logging.error("Alias or Device missing for wifi relay. Please fix and restart.")
                return

            if relay["gpio"] == self.gpio_number:
                self.device = relay["device"]
                self.alias = relay["alias"]
                break

        if self.device == "kasa" and self.alias:
            for alias, ip in output.device_info.items():
                if alias == self.alias:
                    self.ip = ip
                    self.control_device = SmartPlug(self.ip)
                    break

        if self.device == "kasa":
            if self.state == 0:
                asyncio.run(self.turn_off_kasa_device())
            else:
                asyncio.run(self.turn_on_kasa_device())

    async def discover_devices(self):
        devices = await Discover.discover(discovery_timeout=10)
        device_info = {}
        for ip, device in devices.items():
            await device.update()
            device_info[device.alias] = ip
        return device_info
    
    async def turn_off_kasa_device(self):
        await self.control_device.turn_off()
        await self.control_device.update()
        #self.control_device.state_information()
        if self.control_device.is_off:
            logging.info(f"Turned off {self.alias}")

    async def turn_on_kasa_device(self):
        await self.control_device.turn_on()
        await self.control_device.update()
        #self.control_device.state_information()
        if self.control_device.is_on:
            logging.info(f"Turned on {self.alias}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    output_instance = output()

