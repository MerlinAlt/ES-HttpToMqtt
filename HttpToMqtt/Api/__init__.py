"""Submodule that manages the REST-API for the HttpToMqtt Server."""

import re
import datetime
from typing import Union
from logging import getLogger

import uvicorn
from fastapi import FastAPI, Response, status

from HttpToMqtt.Types import *

TIMEOUT = 5

log = getLogger(__name__)


def color_string_to_byte_array(color_as_string: str) -> bytearray:
    """
    Convert color string to a bytearray with three bytes, each one
    for the RGB respectively.
    If the specified format is not adhered to then None is returned.

    Parameters
    -------
    color_as_string : str
        String containing the RGB values to be converted to a bytearray.
        Format has to be '#FFFFFF' just containing hex values. Not case-sensitive.

    Returns
    -------
    A bytearray containing the three RGB values.
    If the specified format is not adhered to then None is returned.
    """
    res = re.match("#[0-9a-fA-F]{6}", color_as_string)
    if res is not None:
        res = res.string[0:7].upper()
        log.debug("Got RGB value: %s", str(res))
        try:
            result = bytearray.fromhex(res[1:])
        except ValueError as err:
            result = None
            log.warning("Got following ValueError while converting %s to bytearray.", str(res[1:]))
            log.warning(str(err))
    else:
        log.warning("The given string '%s' doesn't comply with the expected format. "
                    "Expected format is '#FFFFFF'", color_as_string)
        result = None
    return result


class Api:
    """
    Main class of the Api submodule.

    ...

    Attributes
    ----------

    ip : str
        IP address of the host from the HttpToMqtt Server.
    port : int
        Port on which the HttpToMqtt Server is running.
    mqtt : Mqtt
        MQTT module that manages the MQTT communication
        between the HttpToMqtt Server and ESP32s
    data_manager : DataManager
        Object representing the data manager
        that adds, updates, finds and deletes data from the JSON database.
    """

    app = FastAPI()

    def __init__(self, ip: str, port: int, mqtt, data_manager):
        """Initialize an Api object which handles the REST-API"""
        self.ip = ip
        self.port = port
        self.mqtt = mqtt
        self.data_manager = data_manager
        self.__create_paths()

    def run(self):
        """Run the REST-API."""
        uvicorn.run("HttpToMqtt.Api:Api.app", host=self.ip, port=self.port, log_level="info")

    # pylint: disable=too-many-statements
    def __create_paths(self):
        """Create all paths for the API."""

        def __validate_turn_on_off_parameters(conf: Union[TurnOn, TurnOff],
                                              mac_address: str) -> (int, str):
            if mac_address is None:
                return (status.HTTP_404_NOT_FOUND,
                        f"The shelf with number {conf.ShelfNumber} was not found in our database "
                        f"or check if an ESP32 has been assigned to this ShelfNumber.")

            if conf.PositionId > 255 or conf.PositionId < 0:
                return (status.HTTP_400_BAD_REQUEST,
                        f"The PositionId {conf.PositionId} is either smaller than one or bigger "
                        f"than 255. The ID must be an int in range 0-255 in order to be able to be "
                        f"casted to a byte.")

            if not self.data_manager.position_id_exists(conf.ShelfNumber, conf.PositionId):
                return (status.HTTP_404_NOT_FOUND,
                        f"The position with ID {conf.PositionId} in the shelf with number "
                        f"{conf.ShelfNumber} was not found in our database.")
            return status.HTTP_200_OK, ""

        @self.app.post("/light/turnOn")
        def turn_on(conf: TurnOn, response: Response):
            """Turn on all LEDs of a position in a shelf."""
            mac_address: str = self.data_manager.get_mac_address_by_shelf_number(conf.ShelfNumber)
            response.status_code, ret_str = __validate_turn_on_off_parameters(conf, mac_address)
            if response.status_code != status.HTTP_200_OK:
                return ret_str
            colors_byte_array = color_string_to_byte_array(conf.Color)
            if colors_byte_array is None:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return (f"The parameter Color '{conf.Color}' doesn't comply with the expected "
                        f"format. Expected format is '#FFFFFF'")
            leds = self.data_manager.get_leds_by_shelf_number_and_position_id(conf.ShelfNumber,
                                                                              conf.PositionId)
            if leds is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return (
                    f"The leds in the position with ID {conf.PositionId} in the shelf with number "
                    f"{conf.ShelfNumber} were not found in our database or is None (NullPointer).")

            leds_byte_array = bytearray(leds)
            leds_byte_array.extend(colors_byte_array)
            response.status_code = self.mqtt.publish_with_ack(TIMEOUT, mac_address,
                                                              select_queue="light_ack",
                                                              topic=f"pbl/{mac_address}/light/set",
                                                              payload=leds_byte_array)

            if response.status_code == status.HTTP_504_GATEWAY_TIMEOUT:
                return (f"Timeout warning! ESP32 with the Mac_Address {mac_address} didn't "
                        f"respond in time.")
            if response.status_code == status.HTTP_200_OK:
                return (f"Turned LEDs {leds} on on shelf with number {conf.ShelfNumber} "
                        f"in position with ID {conf.PositionId} with color {conf.Color}.")

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            log.warning("Something unexpected happened, while handling /light/turnOn request.")
            return "Something unexpected happened."

        @self.app.post("/light/turnOff")
        def turn_off(conf: TurnOff, response: Response):
            """Turn off all LEDs of a position."""

            mac_address: str = self.data_manager.get_mac_address_by_shelf_number(conf.ShelfNumber)
            response.status_code, ret_str = __validate_turn_on_off_parameters(conf, mac_address)
            if response.status_code != status.HTTP_200_OK:
                return ret_str

            leds = self.data_manager.get_leds_by_shelf_number_and_position_id(conf.ShelfNumber,
                                                                              conf.PositionId)
            if leds is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return (
                    f"The leds in the position with ID {conf.PositionId} in the shelf with number "
                    f"{conf.ShelfNumber} were not found in our database or is None (NullPointer).")

            leds_byte_array = bytearray(leds)
            response.status_code = self.mqtt.publish_with_ack(
                TIMEOUT, mac_address,
                select_queue="light_ack",
                topic=f"pbl/{mac_address}"
                      f"/light/unset",
                payload=leds_byte_array)

            if response.status_code == status.HTTP_504_GATEWAY_TIMEOUT:
                return (f"Timeout warning! ESP32 with the Mac_Address {mac_address} didn't "
                        f"respond in time.")
            if response.status_code == status.HTTP_200_OK:
                return (f"Turned LEDs {leds} off on shelf with number {conf.ShelfNumber} "
                        f"in position with ID {conf.PositionId}.")

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            log.warning("Something unexpected happened, while handling /light/turnOff request.")
            return "Something unexpected happened."

        @self.app.post("/light/turnOnAll")
        def turn_on_all(shelf_number: ShelfSelectionWithColor, response: Response):
            """Turn on all LEDs from all stored positions on a Shelf."""
            mac_address = self.data_manager.get_mac_address_by_shelf_number(
                shelf_number.ShelfNumber)
            if mac_address is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return (f"The shelf with number {shelf_number.ShelfNumber} was not found in our "
                        f"database or check if an ESP32 has been assigned to this ShelfNumber.")

            colors_byte_array = color_string_to_byte_array(shelf_number.Color)
            if colors_byte_array is None:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return ("The parameter Color doesn't comply with the expected "
                        "format. Expected format is '#FFFFFF'")
            response.status_code = self.mqtt.publish_with_ack(
                TIMEOUT, mac_address, select_queue="light_ack",
                topic=f"pbl/{mac_address}/light/allOn",
                payload=bytearray([colors_byte_array[0],
                                   colors_byte_array[1],
                                   colors_byte_array[2]])
            )

            if response.status_code == status.HTTP_504_GATEWAY_TIMEOUT:
                return (f"Timeout warning! ESP32 with the Mac_Address {mac_address} didn't "
                        f"respond in time.")
            if response.status_code == status.HTTP_200_OK:
                return f"Turned all positions on on shelf with number {shelf_number.ShelfNumber}"

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            log.warning("Something unexpected happened, while handling /light/turnOnAll request.")
            return "Something unexpected happened."

        @self.app.post("/light/turnOffAll")
        def turn_off_all(shelf_number: ShelfSelection, response: Response):
            """Turn off all LEDs from all stored positions on a shelf."""
            mac_address = self.data_manager.get_mac_address_by_shelf_number(
                shelf_number.ShelfNumber)
            if mac_address is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return (f"The shelf with number {shelf_number.ShelfNumber} was not found in our "
                        f"database or check if an ESP32 has been assigned to this ShelfNumber.")

            response.status_code = self.mqtt.publish_with_ack(
                TIMEOUT, mac_address, select_queue="light_ack",
                topic=f"pbl/{mac_address}/light/allOff",
                payload=bytearray([])
            )

            if response.status_code == status.HTTP_504_GATEWAY_TIMEOUT:
                return (f"Timeout warning! ESP32 with the Mac_Address {mac_address} didn't "
                        f"respond in time.")
            if response.status_code == status.HTTP_200_OK:
                return f"Turned all positions off on shelf with number {shelf_number.ShelfNumber}"

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            log.warning("Something unexpected happened, while handling /light/turnOffAll request.")
            return "Something unexpected happened."

        def __validate_set_unset_parameters(conf: Union[SetLED, UnsetLED]) -> (int, str):
            if not self.data_manager.mac_address_exists(conf.Mac_Address):
                return (status.HTTP_404_NOT_FOUND,
                        f"The shelf with the MAC-Address {conf.Mac_Address} "
                        f"was not found in our database.")
            for led in conf.LEDs:
                if led > 255 or led < 0:
                    return (status.HTTP_400_BAD_REQUEST,
                            f"The parameter LED {led} in the given LED Array {conf.LEDs} is either "
                            f"smaller than one or bigger than 255. LED must be an int in range "
                            f"0-255 in order to be able to be casted to a byte.")
            return status.HTTP_200_OK, ""

        @self.app.post("/light/setLEDs")
        def set_leds(conf: SetLED, response: Response):
            """Turn on specified LED on the specified shelf independently of a position ID."""
            response.status_code, ret_str = __validate_set_unset_parameters(conf)
            if response.status_code != status.HTTP_200_OK:
                return ret_str

            colors_byte_array = color_string_to_byte_array(conf.Color)
            if colors_byte_array is None:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return (f"The parameter Color '{conf.Color}' doesn't comply with the expected "
                        f"format. Expected format is '#FFFFFF'")

            leds_byte_array = bytearray(conf.LEDs)
            leds_byte_array.extend(colors_byte_array)
            response.status_code = self.mqtt.publish_with_ack(
                TIMEOUT, conf.Mac_Address, select_queue="light_ack",
                topic=f"pbl/{conf.Mac_Address}/light/set",
                payload=leds_byte_array
            )

            if response.status_code == status.HTTP_504_GATEWAY_TIMEOUT:
                return (f"Timeout warning! ESP32 with the Mac_Address {conf.Mac_Address} didn't "
                        f"respond in time.")
            if response.status_code == status.HTTP_200_OK:
                return (f"Set LEDs {conf.LEDs} on ESP32 with Mac_Address {conf.Mac_Address} "
                        f"with color {conf.Color}")

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            log.warning("Something unexpected happened, while handling /light/setLEDs request.")
            return "Something unexpected happened."

        @self.app.post("/light/unsetLEDs")
        def unset_leds(conf: UnsetLED, response: Response):
            """Turn off specified LED on the specified shelf independently of a position ID."""
            response.status_code, ret_str = __validate_set_unset_parameters(conf)
            if response.status_code != status.HTTP_200_OK:
                return ret_str

            leds_byte_array = bytearray(conf.LEDs)
            response.status_code = self.mqtt.publish_with_ack(
                TIMEOUT, conf.Mac_Address, select_queue="light_ack",
                topic=f"pbl/{conf.Mac_Address}/light/unset",
                payload=leds_byte_array
            )

            if response.status_code == status.HTTP_504_GATEWAY_TIMEOUT:
                return (f"Timeout warning! ESP32 with the Mac_Address {conf.Mac_Address} didn't "
                        f"respond in time.")
            if response.status_code == status.HTTP_200_OK:
                return f"Unset LEDs {conf.LEDs} on ESP32 with Mac_Address {conf.Mac_Address}."

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            log.warning("Something unexpected happened, while handling /light/unSetLEDs request.")
            return "Something unexpected happened."

        def __validate_shelf(shelf_position: Union[ShelfPosition, DeletePosition],
                             shelf: Shelf) -> (int, str):
            if shelf is None:
                return (status.HTTP_404_NOT_FOUND,
                        f"The shelf with number {shelf_position.ShelfNumber} was not found in our "
                        f"database or check if an ESP32 has been assigned to this ShelfNumber.")
            if shelf_position.PositionId > 255 or shelf_position.PositionId < 0:
                return (status.HTTP_400_BAD_REQUEST,
                        f"The PositionId {shelf_position.PositionId} is either smaller than one or "
                        f"bigger than 255. The ID must be an int in range 0-255 in order to be "
                        f"able to be casted to a byte.")
            return status.HTTP_200_OK, ""

        def __publish_create_update_position(shelf_position: ShelfPosition, mac_address: str,
                                             create: bool):
            list_of_int: list[int] = [shelf_position.PositionId]
            list_of_int.extend(shelf_position.LEDs)
            if create:
                status_code = self.mqtt.publish_with_ack(
                    TIMEOUT, mac_address, select_queue="config_ack",
                    topic=f"pbl/{mac_address}/config/create_Position",
                    payload=bytearray(list_of_int)
                )
            else:
                status_code = self.mqtt.publish_with_ack(
                    TIMEOUT, mac_address, select_queue="config_ack",
                    topic=f"pbl/{mac_address}/config/update_Position",
                    payload=bytearray(list_of_int)
                )

            if status_code == status.HTTP_504_GATEWAY_TIMEOUT:
                if create:
                    return (status.HTTP_504_GATEWAY_TIMEOUT,
                            f"Timeout warning! ESP32 with the Mac_Address {mac_address} didn't "
                            f"respond in time. Cannot guarantee shelf position was created!")

                return (status.HTTP_504_GATEWAY_TIMEOUT,
                        f"Timeout warning! ESP32 with the Mac_Address {mac_address} didn't "
                        f"respond in time. Cannot guarantee shelf position was updated!")
            return status_code, ""

        @self.app.put("/light/createPosition")
        def create_position(shelf_position: ShelfPosition, response: Response):
            """Create Position for a shelf."""
            mac_address = self.data_manager.get_mac_address_by_shelf_number(
                shelf_position.ShelfNumber
            )
            if mac_address is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return (f"The shelf with number {shelf_position.ShelfNumber} was not found in our "
                        f"database or check if an ESP32 has been assigned to this ShelfNumber.")
            if self.data_manager.position_id_exists(shelf_position.ShelfNumber,
                                                    shelf_position.PositionId):
                response.status_code = status.HTTP_406_NOT_ACCEPTABLE
                return (
                    f"The position with ID {shelf_position.PositionId} in the shelf with "
                    f"number {shelf_position.ShelfNumber} "
                    f"already exists so cannot create position. Maybe you are trying to update an "
                    f"existing position? Then use the route light/updatePosition")
            shelf = self.data_manager.get_shelf_by_shelf_number(shelf_position.ShelfNumber)
            response.status_code, ret_str = __validate_shelf(shelf_position, shelf)
            if response.status_code != status.HTTP_200_OK:
                return ret_str
            shelf = self.data_manager.get_shelf_by_shelf_number(shelf_position.ShelfNumber)
            response.status_code, ret_str = __validate_shelf(shelf_position, shelf)
            if response.status_code != status.HTTP_200_OK:
                return ret_str

            if self.data_manager.leds_exists(shelf_position.LEDs, shelf_position.ShelfNumber):
                response.status_code = status.HTTP_406_NOT_ACCEPTABLE
                return (f"Cannot create position because one or more of the sent LEDs "
                        f"{shelf_position.LEDs} is already being used by another shelf position "
                        f"in the shelf with number {shelf_position.ShelfNumber}. "
                        f"Try using another LED array.")

            response.status_code, ret_str = __publish_create_update_position(shelf_position,
                                                                             mac_address,
                                                                             True)
            if ret_str != "":
                return ret_str

            if response.status_code == status.HTTP_200_OK:
                if self.data_manager.add_position(shelf, shelf_position):
                    return (f"Added position with ID {shelf_position.PositionId} on shelf with "
                            f"number {shelf_position.ShelfNumber} with LEDs {shelf_position.LEDs}.")

                response.status_code = status.HTTP_406_NOT_ACCEPTABLE
                return (f"Received an ACK from ESP32 but couldn't add position with ID "
                        f"{shelf_position.PositionId} on shelf with number "
                        f"{shelf_position.ShelfNumber} with LEDs {shelf_position.LEDs}.")

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            log.warning("Something unexpected happened, while handling "
                        "/light/createPosition request.")
            return "Something unexpected happened."

        @self.app.put("/light/createShelf")
        def create_shelf(shelf: Shelf, response: Response):
            """
            Create a Shelf in the database. For this there must be an ESP32
            that has registered (exists in the database) and is available
            (isUsed == False) and the given Shelf number cannot already
            exist in the database.
            Positions should be an empty list of ShelfPositions
            (Positions: List[ShelfPosition] = []).
            """
            if self.data_manager.shelf_exists(shelf.ShelfNumber):
                response.status_code = status.HTTP_406_NOT_ACCEPTABLE
                return (f"Cannot create Shelf because the given shelf number {shelf.ShelfNumber} "
                        f"is already being used. Try using another shelf number.")
            if not self.data_manager.mac_address_exists(shelf.Mac_Address):
                response.status_code = status.HTTP_404_NOT_FOUND
                return (f"Cannot create Shelf because the given MAC-address {shelf.Mac_Address} "
                        "doesn't exist in our database, which means that the ESP32 with this "
                        "MAC-address hasn't registered to the database.")
            esp32 = self.data_manager.get_esp32_by_mac_address(shelf.Mac_Address)
            if esp32 is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return (f"Cannot create Shelf because the given MAC-address {shelf.Mac_Address} "
                        "doesn't exist in our database, which means that the ESP32 with this "
                        "MAC-address hasn't registered to the database.")
            if esp32.isUsed:
                response.status_code = status.HTTP_406_NOT_ACCEPTABLE
                return (f"Cannot create Shelf because the ESP32 with given MAC-address "
                        f"{shelf.Mac_Address} "
                        f"is already being used by another Shelf.")
            if self.data_manager.add_shelf(shelf):
                response.status_code = status.HTTP_200_OK
                return f"Successfully created Shelf {shelf}!"
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return f"Couldn't create Shelf {shelf}. Check message from HttpToMqtt Server."

        @self.app.put("/light/updatePosition")
        def update_position(shelf_position: ShelfPosition, response: Response):
            """Update a position on a shelf."""
            mac_address = self.data_manager.get_mac_address_by_shelf_number(
                shelf_position.ShelfNumber
            )
            if mac_address is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return (f"The shelf with number {shelf_position.ShelfNumber} was not found in our "
                        f"database or check if an ESP32 has been assigned to this ShelfNumber.")
            if not self.data_manager.position_id_exists(shelf_position.ShelfNumber,
                                                        shelf_position.PositionId):
                response.status_code = status.HTTP_406_NOT_ACCEPTABLE
                return (
                    f"The position with ID {shelf_position.PositionId} in the shelf "
                    f"with number {shelf_position.ShelfNumber} "
                    f"doesn't exist so cannot update position. Maybe you are trying to create a "
                    f"position? Then use the route light/createPosition")
            shelf = self.data_manager.get_shelf_by_shelf_number(shelf_position.ShelfNumber)
            response.status_code, ret_str = __validate_shelf(shelf_position, shelf)
            if response.status_code != status.HTTP_200_OK:
                return ret_str

            if self.data_manager.leds_exists_exclusive(shelf_position):
                response.status_code = status.HTTP_406_NOT_ACCEPTABLE
                return (f"Cannot create position because one or more of the sent LEDs "
                        f"{shelf_position.LEDs}  is already being used by another shelf position "
                        f"in the shelf with number {shelf_position.ShelfNumber}. "
                        f"Try using another LED array.")

            response.status_code, ret_str = __publish_create_update_position(shelf_position,
                                                                             mac_address,
                                                                             False)
            if ret_str != "":
                return ret_str

            if response.status_code == status.HTTP_200_OK:
                if self.data_manager.update_position(shelf, shelf_position):
                    return (f"Updated position with ID {shelf_position.PositionId} on shelf with "
                            f"number {shelf_position.ShelfNumber} with LEDs {shelf_position.LEDs}.")

                response.status_code = status.HTTP_406_NOT_ACCEPTABLE
                return (f"Received an ACK from ESP32 but couldn't add position with ID "
                        f"{shelf_position.PositionId} on shelf with number "
                        f"{shelf_position.ShelfNumber} with LEDs {shelf_position.LEDs}.")

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            log.warning("Something unexpected happened, while "
                        "handling /light/updatePosition request.")
            return "Something unexpected happened."

        # @self.app.put("/light/updateShelf")
        # def update_shelf(shelf_position: ShelfPosition, response: Response):
        #
        #    pass

        @self.app.delete("/light/deletePosition")
        def delete_position(shelf_position: DeletePosition, response: Response):
            """Delete a position on a shelf."""
            mac_address = self.data_manager.get_mac_address_by_shelf_number(
                shelf_position.ShelfNumber
            )
            if mac_address is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return (f"The shelf with number {shelf_position.ShelfNumber} was not found in our "
                        f"database or check if an ESP32 has been assigned to this ShelfNumber.")
            if not self.data_manager.position_id_exists(shelf_position.ShelfNumber,
                                                        shelf_position.PositionId):
                response.status_code = status.HTTP_406_NOT_ACCEPTABLE
                return (
                    f"The position with ID {shelf_position.PositionId} in the shelf "
                    f"with number {shelf_position.ShelfNumber} "
                    f"doesn't exist so cannot delete position.")
            shelf = self.data_manager.get_shelf_by_shelf_number(shelf_position.ShelfNumber)
            response.status_code, ret_str = __validate_shelf(shelf_position, shelf)
            if response.status_code != status.HTTP_200_OK:
                return ret_str

            shelf_position_to_be_deleted = \
                self.data_manager.get_position_by_shelf_number_and_position_id(
                    shelf.ShelfNumber,
                    shelf_position.PositionId)
            if shelf_position_to_be_deleted is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return (f"Didn't find position to be deleted with the position ID "
                        f"{shelf_position.PositionId} in Shelf with the shelf_number "
                        f"{shelf.ShelfNumber}")

            list_of_int: list[int] = [shelf_position_to_be_deleted.PositionId]
            response.status_code = self.mqtt.publish_with_ack(
                TIMEOUT, mac_address, select_queue="config_ack",
                topic=f"pbl/{mac_address}/config/delete_Position",
                payload=bytearray(list_of_int)
            )

            if response.status_code == status.HTTP_504_GATEWAY_TIMEOUT:
                return (f"Timeout warning! ESP32 with the Mac_Address {mac_address} didn't "
                        f"respond in time. Cannot guarantee shelf position was deleted!")
            if response.status_code == status.HTTP_200_OK:
                if self.data_manager.delete_position(shelf, shelf_position_to_be_deleted):
                    return (f"Deleted position with ID {shelf_position_to_be_deleted.PositionId} "
                            f"on shelf with number {shelf_position_to_be_deleted.ShelfNumber} "
                            f"with LEDs {shelf_position_to_be_deleted.LEDs}.")

                response.status_code = status.HTTP_406_NOT_ACCEPTABLE
                return ("Received an ACK from ESP32 but couldn't delete position "
                        f"with ID {shelf_position_to_be_deleted.PositionId} on shelf with number "
                        f"{shelf_position_to_be_deleted.ShelfNumber} with LEDs "
                        f"{shelf_position_to_be_deleted.LEDs}.")

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            log.warning("Something unexpected happened, while "
                        "handling /light/deletePosition request.")
            return "Something unexpected happened."

        @self.app.delete("/light/deleteShelf")
        def delete_shelf(shelf_number: ShelfSelection, response: Response):
            """
            Delete the Shelf with the given shelf number. All configuration stored in
            the ESP32 assigned to the deleted Shelf will be reset.
            """
            shelf = self.data_manager.get_shelf_by_shelf_number(shelf_number.ShelfNumber)
            if not self.data_manager.shelf_exists(shelf_number.ShelfNumber) or shelf is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return "Cannot delete Shelf because it was not found in our database."

            response.status_code = self.mqtt.publish_with_ack(
                TIMEOUT + 20, shelf.Mac_Address,
                select_queue="config_ack",
                topic=f"pbl/{shelf.Mac_Address}/config/reset",
                payload=bytearray([])
            )
            if response.status_code == status.HTTP_504_GATEWAY_TIMEOUT:
                return (f"Timeout warning! ESP32 with the Mac_Address {shelf.Mac_Address} didn't "
                        f"respond in time. Cannot guarantee shelf was deleted!")
            if response.status_code == status.HTTP_200_OK:
                if self.data_manager.delete_shelf_by_shelf_number(shelf.ShelfNumber):
                    return f"Deleted shelf with shelf number {shelf.ShelfNumber}."

                response.status_code = status.HTTP_406_NOT_ACCEPTABLE
                return (f"Received an ACK from ESP32 but couldn't delete shelf with number "
                        f"{shelf.ShelfNumber}.")

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            log.warning("Something unexpected happened, while handling /light/deleteShelf request.")
            return "Something unexpected happened."

        @self.app.get("/light/getPositions/{shelf_number}")
        def get_positions(shelf_number: int, response: Response):
            """Get all positions of a shelf."""
            mac_address = self.data_manager.get_mac_address_by_shelf_number(shelf_number)
            if mac_address is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return (f"The shelf with number {shelf_number} was not found in our "
                        f"database or check if an ESP32 has been assigned to this ShelfNumber.")
            shelf = self.data_manager.get_shelf_by_shelf_number(shelf_number)

            response.status_code = status.HTTP_200_OK
            return shelf.json()

        @self.app.get("/light/getShelves")
        def get_shelves(response: Response):
            """Get all shelves."""
            shelves = self.data_manager.get_shelf_array()
            if shelves is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return "The ShelfArray of the DB is None or empty."

            response.status_code = status.HTTP_200_OK
            return shelves.json()

        @self.app.get("/light/getMACAddresses")
        def get_mac_addresses(response: Response):
            """
            Get all unused MAC-Addresses from the database
            """
            esp32s = self.data_manager.get_esp32_array()
            unused_mac_addresses = []
            for esp32 in esp32s.ESP32s:
                if not esp32.isUsed:
                    unused_mac_addresses.append(esp32.Mac_Address)
            if not unused_mac_addresses:
                response.status_code = status.HTTP_404_NOT_FOUND
                return "Sorry, there are no unused ESP32s for your new shelf."

            response.status_code = status.HTTP_200_OK
            return unused_mac_addresses

        @self.app.get("/light/getESP32")
        def get_esp32_config(mac_address : str, shelf_number: int, response: Response):
            """
            Route to get all stored data on the ESP32 with the specified MAC-address
            into the shelf with the specified shelf number. This route prepares an empty shelf that
            will sequentially receive all the sent positions from the ESP32.
            In order to use this route you have to:
            -send an existing MAC-address
            -the MAC-address has to be assigned to the given shelf number
            -or the shelf number is a new one but the MAC-address is not assigned to another shelf
            """
            if not self.data_manager.mac_address_exists(mac_address):
                response.status_code = status.HTTP_404_NOT_FOUND
                return (f"Cannot get data from ESP32 with MAC-address "
                        f"{mac_address} because it was "
                        f"not found in our database.")

            esp32 = self.data_manager.get_esp32_by_mac_address(mac_address)

            if mac_address == self.data_manager.get_mac_address_by_shelf_number(shelf_number):
                if self.data_manager.delete_shelf_by_shelf_number(shelf_number):
                    if self.data_manager.add_shelf(
                            Shelf(ShelfNumber=shelf_number,
                                  Mac_Address=mac_address,
                                  Positions=[])):
                        response.status_code = self.mqtt.publish_with_ack(
                            TIMEOUT, mac_address,
                            select_queue="config_ack",
                            topic=f"pbl/{mac_address}/config/get",
                            payload=bytearray([])
                        )
                        if response.status_code == status.HTTP_504_GATEWAY_TIMEOUT:
                            return (f"Timeout warning! ESP32 with the Mac_Address "
                                    f"{mac_address} didn't respond in time "
                                    f"or during the reset process a timeout occurred. It is not "
                                    f"guaranteed that all positions were reset on the ESP32.")
                        if response.status_code == status.HTTP_200_OK:
                            return (f"Sent get message to ESP32 with MAC-address "
                                    f"{mac_address}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return (f"Deleted existing shelf with shelf number "
                            f"{shelf_number} but couldn't create a new one "
                            f"with the shelf number {shelf_number} and the "
                            f"MAC-address {mac_address} in order to put the "
                            f"sent data into it. Try it again.")

            if not self.data_manager.shelf_exists(shelf_number):
                if esp32.isUsed:
                    esp32.isUsed = False
                if self.data_manager.add_shelf(
                        Shelf(ShelfNumber=shelf_number,
                              Mac_Address=mac_address,
                              Positions=[])):
                    response.status_code = self.mqtt.publish_with_ack(
                        TIMEOUT, mac_address,
                        select_queue="config_ack",
                        topic=f"pbl/{mac_address}/config/get",
                        payload=bytearray([])
                    )
                    if response.status_code == status.HTTP_504_GATEWAY_TIMEOUT:
                        return (f"Timeout warning! ESP32 with the Mac_Address "
                                f"{mac_address} didn't respond in time. A "
                                f"new shelf was created but it is not guaranteed that all "
                                f"positions were gotten from the ESP32.")
                    if response.status_code == status.HTTP_200_OK:
                        return (f"Sent get message to ESP32 with MAC-address "
                                f"{mac_address}")
                if not esp32.isUsed:
                    esp32.isUsed = True
                response.status_code = status.HTTP_400_BAD_REQUEST
                return (f"Couldn't send get message to ESP32 with MAC-address "
                        f"{mac_address} because couldn't add a shelf that "
                        f"would receive the put data.")
            response.status_code = status.HTTP_400_BAD_REQUEST
            mac_address = self.data_manager.get_mac_address_by_shelf_number(shelf_number)
            return (f"Couldn't send get message to ESP32 with MAC-address "
                    f"{mac_address} because tried to get data from an ESP32 "
                    f"that is assigned to another shelf. The shelf with the number "
                    f"{shelf_number} is assigned to the ESP32 with the MAC "
                    f"{mac_address}")

        @self.app.post("/light/resetESP32")
        def reset_esp32(esp32_to_be_reset: ResetESP32, response: Response):
            """
            Route to reset the stored data on the ESP32 with the specified
            MAC-Address in the post body.
            """
            response.status_code = self.mqtt.publish_with_ack(
                TIMEOUT + 20, esp32_to_be_reset.Mac_Address,
                select_queue="config_ack",
                topic=f"pbl/{esp32_to_be_reset.Mac_Address}/config/reset",
                payload=bytearray([])
            )
            if response.status_code == status.HTTP_504_GATEWAY_TIMEOUT:
                return (f"Timeout warning! ESP32 with the Mac_Address "
                        f"{esp32_to_be_reset.Mac_Address} didn't respond in time or during the "
                        f"reset process a timeout occurred. It is not guaranteed that all "
                        f"positions were reset on the ESP32.")
            if response.status_code == status.HTTP_200_OK:
                return f"Reset all positions on ESP32 with address {esp32_to_be_reset.Mac_Address}"

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            log.warning("Something unexpected happened, while handling /light/resetESP32 request.")
            return "Something unexpected happened."

        @self.app.post("/light/loadESP32")
        def load_esp32(shelf_number: ShelfSelection, response: Response):
            """
            Route to load the entire content of a shelf with the given shelf_number
            to the ESP32 assigned to it.
            """
            mac_address = self.data_manager.get_mac_address_by_shelf_number(
                shelf_number.ShelfNumber
            )
            if mac_address is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return (f"The shelf with number {shelf_number.ShelfNumber} was not found in our "
                        f"database or check if an ESP32 has been assigned to this ShelfNumber.")
            positions = self.data_manager.get_positions_by_shelf_number(shelf_number.ShelfNumber)
            response.status_code = 200
            timeout_happened = False
            log.debug("Before starting loading process, time = %s", str(datetime.datetime.now()))
            for position in positions:
                list_of_int: list[int] = [position.PositionId]
                list_of_int.extend(position.LEDs)
                response.status_code = self.mqtt.publish_with_ack(
                    TIMEOUT, mac_address, select_queue="config_ack",
                    topic=f"pbl/{mac_address}/config/update_Position",
                    payload=bytearray(list_of_int)
                )
                if response.status_code == status.HTTP_504_GATEWAY_TIMEOUT:
                    timeout_happened = True

            log.debug("After loading process, time = %s", str(datetime.datetime.now()))

            if response.status_code == status.HTTP_504_GATEWAY_TIMEOUT or timeout_happened:
                return (f"Timeout warning! ESP32 with the Mac_Address {mac_address} didn't "
                        f"respond in time or during the loading process a timeout occurred. It "
                        f"is not guaranteed that all positions were loaded to the ESP32.")
            if response.status_code == status.HTTP_200_OK:
                return f"Loaded all positions to ESP32 with address {mac_address}"

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            log.warning("Something unexpected happened, while handling /light/loadESP32 request.")
            return "Something unexpected happened."
