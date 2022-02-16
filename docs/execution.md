# Run HttpToMqtt
## Debug Mode
To execute the module in debug mode use the `-d` or `--debug` option. For a full list of available options use the command `python -m HttpToMqtt -h`.

## Configure MQTT client
To configure the MQTT client use a config file as is shown with the Template that can be found [here](Templates/config.json). The path to the config file can be specified with the `-c` or `--config` option. The Default is `HttpToMqtt/Mqtt/mqtt_config.json`. If the file doesn't exist an empty database is initialized in that directory.

## Configure storage location
The location of the storage can be configured with the `-s` or `--storage` option. For example `python -m HttpToMqtt -s Storage/db.json`. The path must end with a json-file. The module automatically creates a backup file in the same directory. The default directory is `HttpToMqtt/DataManager/db.json`.

## Configure REST-API
With the option `-a` or `--address` the host address for the REST-API can be configured. The option `-p` or `--port` specify to which port the REST-API should be bound. The default is `127.0.0.1:8000`.
