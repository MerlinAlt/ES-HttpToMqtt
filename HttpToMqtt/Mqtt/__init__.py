"""Submodule that manages the MQTT communication between the HttpToMqtt Server and ESP32s"""

import json
from logging import getLogger
import random
import time
import paho.mqtt.client as mqtt
from HttpToMqtt.Types import ACK, ESP32, ShelfPosition, Shelf

log = getLogger(__name__)


class Mqtt:
    """
        A class to represent a MQTT module that has a MQTT client
        and access to a JSON database.

        ...

        Attributes
        ----------
        conf_path : str
            Path to the configuration JSON file that contains
            all the necessary information to set up the MQTT client.
        data_manager : DataManager
            Object representing the data manager
            that adds, updates, finds and deletes data from the JSON database.
        light_ack_queue : list[ACK]
            Queue for the ACKs coming from all operations over the pbl/+/light MQTT topic.
        config_ack_queue : list[ACK]
            Queue for the ACKs coming from all operations over the pbl/+/config MQTT topic.
        config : dict
            Object representing the deserialized JSON file in conf_path.
        client : paho.mqtt.client.Client
            MQTT client that sends and receives messages to and from the ESP32s.
    """

    def __init__(self, path: str, data_manager):
        """
        Constructs an instance of a MQTT module that has access to stored
        data in a JSON file.

        Parameters
        ----------
        path : str
            Path to the configuration JSON file that contains
            all the necessary information to set up the MQTT client.
        data_manager : DataManager
            Object representing the data manager
            that adds, updates, finds and deletes data from the JSON database.
        """

        self.conf_path: str = path
        self.data_manager = data_manager
        self.config_ack_queue: list[ACK] = []
        self.light_ack_queue: list[ACK] = []
        with open(self.conf_path, encoding="utf-8") as fp:
            self.config = json.load(fp)

        self.client = mqtt.Client()

    def run(self) -> mqtt.Client:
        """
        Registers the callbacks for the MQTT client and connects it to the
        specified MQTT-broker in the configuration JSON file. Then it starts
        the loops that receive messages and handles them.

        Returns
        -------
        The reference to the MQTT client of the MQTT module.
        """

        self.__create_callbacks()
        self.client.connect(self.config["server"],
                            self.config["port"],
                            self.config["keepalive"])
        log.info("Successfully connected MQTT-Client to %s on port %s.",
                 str(self.config['server']), str(self.config['port']))
        self.client.loop_start()
        return self.client

    def publish_with_ack(self, timeout: int, mac_address: str, select_queue: str, topic: str,
                         payload: bytearray) -> int:
        """
        Publishes a MQTT message (payload) to the specified topic using the
        specified select_queue ("light_ack" or "config_ack") in order to
        get ACKs from the ESP32 to which the message was sent.

        If in 'timeout' seconds an ACK has not returned from the ESP32
        to which the message was sent the status code 504 (HTTP_504_GATEWAY_TIMEOUT)
        is returned. After an ACK has come the status code 200 (HTTP_200_OK) is returned.

        Parameters
        ----------
        timeout : int
            Seconds to wait for an ACK.
        mac_address : str
            String representing the MAC-address of the ESP32 that the message is being sent to.
        select_queue : str
            String to choose which queue should be used for waiting for the ACK. There are just
            two possible values, "light_ack" or "config_ack".
        topic : str
            MQTT topic to which the message should be published.
        payload : bytearray
            Byte array containing the raw data to be sent.

        Returns
        -------
        A status code that depends on how the operation went. If in 'timeout' seconds
        an ACK has not returned from the ESP32 to which the message was sent the status
        code 504 (HTTP_504_GATEWAY_TIMEOUT) is returned. After an ACK has come the
        status code 200 (HTTP_200_OK) is returned.
        """

        # choosing right queue
        queue = None
        if select_queue == "light_ack":
            queue = self.light_ack_queue
        if select_queue == "config_ack":
            queue = self.config_ack_queue
        if queue is None:
            raise Exception("Didn't choose the right queue: either light_ack or config_ack")

        # generating a random ID for the outgoing ACK
        # in the range between 0 and 255 because the IDs are
        # meant to be a single byte
        random_ack_id = random.randint(0, 255)
        log.debug("random_ack_id = %d", random_ack_id)

        # creating the outgoing ACK
        outgoing_ack = ACK(Mac_Address=mac_address, ACK_id=random_ack_id)

        # checking if the created outgoing_ack doesn't exist in the
        # light_ack_queue. If it does then a new ID is generated.
        # repeat until we have an outgoing_ack that is unique at the time of sending
        while outgoing_ack in queue:
            log.debug("set_leds(): had to find another random_ack_id!")
            random_ack_id = random.randint(0, 255)
            outgoing_ack = ACK(Mac_Address=mac_address, ACK_id=random_ack_id)

        log.debug("outgoing_ack looks like this --> %s", str(outgoing_ack))

        # publishing the command to the esp32 with the mac_address
        # assigned to the provided ShelfNumber
        payload_with_ack_id = bytearray([outgoing_ack.ACK_id])
        log.debug("before extending %s", str(payload_with_ack_id))
        payload_with_ack_id.extend(payload)
        log.debug("after extending %s", str(payload_with_ack_id))
        self.client.publish(topic, payload=payload_with_ack_id)

        # registering a time_stamp to check for timeouts
        timestamp = time.time()
        # waiting until received outgoing_ack
        while outgoing_ack not in queue:
            # checking timeout
            if time.time() - timestamp > timeout:
                log.debug("Printing queue before timeout --> %s", str(queue))
                return 504  # HTTP_504_GATEWAY_TIMEOUT
        log.debug("Received ACK with ID %d! Removing %s", outgoing_ack.ACK_id, str(outgoing_ack))
        queue.remove(outgoing_ack)
        return 200

    def __create_callbacks(self):
        """
        Creates all callbacks that implement all needed functionality concerning
        the communication between the HTTP server and the ESP32s over MQTT.

        Returns
        -------
        None
        """

        def on_connect(client, _userdata, _flags, rc):
            """
            The callback for when the client receives a CONNACK response from the server.
            Here the subscriptions take place.

            Parameters
            -------
            client : Client
                Client instance that is calling the callback.
            _userdata :
                User data of any type and can be set when creating a new _client
                instance or with user_data_set(userdata).
            _flags : response flags sent by the broker
            rc : int
                Result code from the connection process.

            Returns
            -------
            None
            """

            log.info("Connected with result code %s", str(rc))

            # Subscribing in on_connect() means that if we lose the connection and
            # reconnect then subscriptions will be renewed.
            client.subscribe("pbl/#", 1)
            client.subscribe("pbl/+/light/ack", 1)
            client.subscribe("pbl/+/config/ack", 1)
            client.subscribe("pbl/register", 1)
            client.subscribe("pbl/+/config/put", 1)
            client.subscribe("pbl/+/config/offline", 1)

        def on_message(_client, _userdata, msg):
            """
            The callback for when a PUBLISH-message is received from the server.
            In this implementation just received information and the topic is printed.
            All other callbacks are directly linked to their specific topics and
            are not handled in this more general callback. The printing is more
            for debugging and observing purposes.

            Parameters
            -------
            _client :
                Client instance that is calling the callback.
            _userdata :
                User data of any type and can be set when creating a new _client
                instance or with user_data_set(userdata).
            msg :
                Object containing the topic (msg.topic) and the bytes (msg.payload)
                sent to this.

            Returns
            -------
            None
            """
            log.debug("on_message(): Received %s on %s", str(msg.payload), msg.topic)

        def receive_register(_client, _userdata, msg):
            """
            Callback that registers an ESP32 that connected to the MQTT broker
            used for the Pick By Light system. In this way the database stores
            information about the registered ESP32s.

            In case the ESP32 is already registered its attribute isOnline is set to True.
            ESP32s should periodically send a register message in order to store
            their connection status.

            Parameters
            -------
            _client :
                Client instance that is calling the callback.
            _userdata :
                User data of any type and can be set when creating a new client
                instance or with user_data_set(userdata).
            msg :
                Object containing the topic (msg.topic) and the bytes (msg.payload)
                sent to this.

            Returns
            -------
            None
            """

            incoming_mac_address = str(msg.payload)[2:-1]
            if self.data_manager.mac_address_exists(incoming_mac_address):
                esp32 = self.data_manager.get_esp32_by_mac_address(incoming_mac_address)
                esp32.isOnline = True
                self.data_manager.save_data()
                log.debug("ESP32 with %s is back online!", incoming_mac_address)
            else:
                esp32 = ESP32(Mac_Address=incoming_mac_address, isUsed=False, isOnline=True)
                if self.data_manager.add_esp32(esp32):
                    log.info("Successfully added the ESP32 %s to the database!", str(esp32))
                else:
                    log.warning("Couldn't add ESP32 %s to the database.", str(esp32))

        def config_offline(_client, _userdata, msg):
            """
            Callback that registers in the database if an ESP32, which was already registered,
            disgracefully disconnected from the broker. When this happens its attribute isOnline
            is set to False.

            Parameters
            -------
            _client :
                Client instance that is calling the callback.
            _userdata :
                User data of any type and can be set when creating a new _client
                instance or with user_data_set(userdata).
            msg :
                Object containing the topic (msg.topic) and the bytes (msg.payload)
                sent to this.

            Returns
            -------
            None
            """
            split_topic = msg.topic.split('/')
            mac_address = split_topic[1]
            log.debug("config_offline(): Extracted mac_address = %s", mac_address)
            if self.data_manager.mac_address_exists(mac_address):
                esp32 = self.data_manager.get_esp32_by_mac_address(mac_address)
                esp32.isOnline = False
                self.data_manager.save_data()
                log.info("ESP32 with %s disgracefully disconnected!", mac_address)

        def receive_config_ack(_client, _userdata, msg):
            """
            Callback that places an incoming ACK in the config_ack_queue using
            the general receive_ack method.

            Parameters
            -------
            _client :
                Client instance that is calling the callback.
            _userdata :
                User data of any type and can be set when creating a new _client
                instance or with user_data_set(userdata).
            msg :
                Object containing the topic (msg.topic) and the bytes (msg.payload)
                sent to this.

            Returns
            -------
            None
            """
            receive_ack(msg, self.config_ack_queue)

        def receive_light_ack(_client, _userdata, msg):
            """
            Callback that places an incoming ACK in the light_ack_queue using
            the general receive_ack method.

            Parameters
            -------
            _client :
                Client instance that is calling the callback.
            _userdata :
                User data of any type and can be set when creating a new _client
                instance or with user_data_set(userdata).
            msg :
                Object containing the topic (msg.topic) and the bytes (msg.payload)
                sent to this.

            Returns
            -------
            None
            """
            receive_ack(msg, self.light_ack_queue)

        def receive_ack(msg, queue):
            """
            Callback that places an incoming ACK in the specified queue. It extracts
            the needed MAC address from the topic and the ACK ID from the payload.

            Parameters
            -------
            msg :
                Object containing the topic (msg.topic) and the bytes (msg.payload)
                sent to this.
            queue :
                Queue to which the incoming ACK will be appended to.

            Returns
            -------
            None
            """

            split_topic = msg.topic.split('/')
            mac_address = split_topic[1]
            log.debug("receive_ack(): Extracted mac_address = %s", mac_address)
            # ack_id_as_string = str(msg.payload)[2:-1]
            ack_id = int.from_bytes(bytearray([msg.payload[0]]), 'big')
            # ack_id = int.from_bytes(msg.payload, byteorder='big')
            # ack_id = int(str(msg.payload)[2:-1])

            received_ack = ACK(Mac_Address=mac_address, ACK_id=ack_id)
            log.debug("received ack = %s", str(received_ack))
            queue.append(received_ack)
            log.debug("Appended %s to %s", str(received_ack), str(queue))

        def config_put(_client, _userdata, msg):
            """
            Callback used to load entire data from an ESP32 into the database.
            For this to be used there has to be a valid empty (empty because positions will be
            created on the database and not updated, which means that they will not be created if
            their positions IDs already exist) shelf with the MAC-address of the ESP32 sending the
            messages. The ESP32 will start using this topic after it gets a message to the topic
            pbl/MAC-address/config/get. Then it will send a MQTT message for each registered
            position it has and this method config_put will be called for every position.

            Parameters
            -------
            _client :
                Client instance that is calling the callback.
            _userdata :
                User data of any type and can be set when creating a new _client
                instance or with user_data_set(userdata).
            msg :
                Object containing the topic (msg.topic) and the bytes (msg.payload)
                sent to this.

            Returns
            -------
            None
            """
            split_topic = msg.topic.split('/')
            mac_address = split_topic[1]
            log.debug("config_put(): Extracted mac_address = %s", str(mac_address))
            shelf: Shelf = self.data_manager.get_shelf_by_mac_address(mac_address)
            if shelf is None:
                log.warning("Couldn't create position because there is no "
                            "shelf with the MAC-address %s", str(mac_address))
                return
            position_id = int.from_bytes(bytearray([msg.payload[0]]), 'big')
            leds: list[int] = []
            for byte in msg.payload[1:]:
                leds.append(byte)
            if not leds:
                log.warning("Couldn't create position because no LEDs were given for the position. "
                            "In other words, msg.payload didn't have any data after the first "
                            "byte which is the position id.")
                return
            shelf_position: ShelfPosition = ShelfPosition(ShelfNumber=shelf.ShelfNumber,
                                                          PositionId=position_id,
                                                          LEDs=leds)
            if self.data_manager.add_position(shelf, shelf_position):
                log.info("Successfully added position %s "
                         "to shelf with number %d", str(shelf_position), shelf.ShelfNumber)
                return
            log.warning("Couldn't add position %s to shelf with number %d",
                        str(shelf_position), shelf.ShelfNumber)

        # registering callbacks to the specified functions
        self.client.on_connect = on_connect
        self.client.on_message = on_message
        self.client.message_callback_add("pbl/+/light/ack", receive_light_ack)
        self.client.message_callback_add("pbl/+/config/ack", receive_config_ack)
        self.client.message_callback_add("pbl/register", receive_register)
        self.client.message_callback_add("pbl/+/config/put", config_put)
        self.client.message_callback_add("pbl/+/config/offline", config_offline)
