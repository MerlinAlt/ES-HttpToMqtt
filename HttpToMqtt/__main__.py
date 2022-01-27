"""HttpToMqtt Module of pick-by-light project."""
import logging
import sys
import getopt
import os.path
from pathlib import Path
from logging import getLogger

from HttpToMqtt.Api import Api
from HttpToMqtt.DataManager import DataManager
from HttpToMqtt.Mqtt import Mqtt

log = getLogger()

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))

log.addHandler(stream_handler)
log.setLevel(logging.INFO)

conf_path = os.path.join(os.path.dirname(__file__), "Mqtt", "mqtt_config.json")
storage_path = os.path.join(os.path.dirname(__file__), "DataManager", "db.json")

__HELP = ("Usage: HttpToMqtt [OPTIONS]\n"
          "OPTIONS:\n"
          "  -h                              Show this help page and exit.\n"
          "  -c, --config <path_to_config>   Define path to MQTT-Client config.\n"
          "                                  (Default from Package root: Mqtt/mqtt_config.json)\n"
          "  -s, --storage <path_to_storage> Define path to storage file.\n"
          "                                  (Default from Package root: DataManager/db.json)\n"
          "  -a, --address <host-address>    Bind socket to this host. (Default: 127.0.0.1)\n"
          "  -p, --port <host-port>          Bind socket to this port. (Default: 8000)\n"
          "  -d, --debug                     Set log level to debug\n")

HOST_IP = "127.0.0.1"
HOST_PORT = 8000

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:s:p:a:d", ["help", "config", "storage", "port",
                                                                "address", "debug"])
    except getopt.GetoptError:
        print(__HELP)
        sys.exit(2)
    for opt, arg in opts:
        if opt in {"-h", "--help"}:
            print(__HELP)
            sys.exit(0)
        elif opt in {"-c", "--config"}:
            log.debug("Config path: %s", arg)
            conf_path = arg
        elif opt in {"-s", "--storage"}:
            storage_path = arg
        elif opt in {"-a", "--address"}:
            HOST_IP = arg
        elif opt in {"-p", "--port"}:
            HOST_PORT = arg
        elif opt in {"-d", "--debug"}:
            log.setLevel(logging.DEBUG)

    data_manager = DataManager(Path(storage_path))
    mqtt = Mqtt(conf_path, data_manager)
    log.info("Running MQTT Client ...")
    mqtt.run()
    api = Api(HOST_IP, HOST_PORT, mqtt, data_manager)
    log.info("Running API ...")
    api.run()
