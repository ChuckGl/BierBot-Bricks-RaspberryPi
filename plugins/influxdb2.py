from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Variables for InfluxDB connection
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "HwbdLIh6q4OASislKP6WrHqmyaESWhf7507DiC4MsRl4NvA7Q_jPwt7MkXb5oQWyQ3vADxm5g--qgDUMHOXAOA=="
INFLUXDB_ORG = "brewhouse"
INFLUXDB_BUCKET = "bierbot"

class InfluxDBWriter:
    def __init__(self):
        self.url = INFLUXDB_URL
        self.token = INFLUXDB_TOKEN
        self.org = INFLUXDB_ORG
        self.bucket = INFLUXDB_BUCKET
        self.client = InfluxDBClient(url=self.url, token=self.token)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def write_data(self, gpio_number, state):
        point = Point("sensor_data") \
            .tag("gpio_number", gpio_number) \
            .field("state", state)
        
        self.write_api.write(self.bucket, self.org, point)

if __name__ == "__main__":
    main(gpio_number, state)

