"""Submodule that manages the JSON database containing Shelves and ESP32s."""

import datetime
import json
from pathlib import Path
from typing import Optional
from logging import getLogger

from HttpToMqtt.Types import *

log = getLogger(__name__)


class DataManager:
    """
    A class that manages a JSON database that complies to
    the structure of the Class DB in Types/__init__.py.

    ...

    Attributes
    ----------
    __db : DB
        Class containing a Types.ShelfArray object and a Types.ESP32Array object that stores
        all data during runtime and saves it to a JSON file when needed. This DB object is
        referred to as the "database" in the entire documentation. When talking about the
        database it's a reference to this DB object.
    __path_to_json_file : Path
        String with the path to the JSON file that holds the database or in which the database
        has to be stored.
    __path_to_json_file_backup : Path
        String with the path to the JSON file that holds a backup of the database.
    """

    def __init__(self, path_to_json_file: Path):
        """
        Constructs an instance of DataManager.

        Parameters
        -------
        path_to_json_file : Path
            Path object containing the path to the JSON file that holds the database.

        Returns
        --------
        A DataManager object when the specified path ends with '.json'.
        If the specified path leads to an existing file, this has to comply to
        the JSON structure of the Class DB in Types/__init__.py, otherwise an error will occur.
        If the file in the specified path doesn't exist then the DataManager is initialized
        with an empty file/database.
        If the specified path does not end with '.json' then an exception is raised.
        """
        if path_to_json_file.name.endswith('.json'):
            try:
                self.__path_to_json_file = path_to_json_file
                parts = path_to_json_file.parts
                self.__path_to_json_file_backup = Path(*(*parts[:-1],
                                                         parts[-1].replace(".json", "_backup.json"))
                                                       )
                log.debug("self.__path_to_json_file = %s", str(self.__path_to_json_file))
                # creating the database out of the json file.
                log.debug("self.__path_to_json_file_backup = %s",
                          str(self.__path_to_json_file_backup))
                self.__db = DB.parse_file(path_to_json_file)
                self.set_all_esp32s_offline()
                log.info("Initialized DB successfully with path %s", self.__path_to_json_file)
                self.save_data()
                self.save_backup_data()
            except FileNotFoundError:
                self.__db = DB(Shelves=[], ESP32s=[])
                log.info("Couldn't find json file. Initialized DB successfully with empty database.")
                self.save_data()
                self.save_backup_data()

        else:
            raise Exception("The given path name doesn't end with .json! Use a valid .json file!")

    def __save_data_to(self, path):
        """
        Save the data stored in the DB object from the DataManager as JSON to path.
        """
        log.debug("Before file.write() time = %s", str(datetime.datetime.now()))
        with open(path, "wt", encoding="utf-8") as file:
            file.write(json.dumps(json.loads(self.__db.json()), indent=4))
        log.debug("After file.write() time = %s", str(datetime.datetime.now()))

    def save_data(self) -> None:
        """
        Saves the data stored in the DB object from the DataManager as JSON in a text file.
        """
        self.__save_data_to(self.__path_to_json_file)

    def save_backup_data(self) -> None:
        """
        Saves a backup of the data stored in the DB object from the DataManager as JSON in a text file.
        """
        self.__save_data_to(self.__path_to_json_file_backup)

    def shelf_exists(self, shelf_number: int) -> bool:
        """
        Returns True if the given ShelfNumber is found in the database.

        Parameters
        -------
        shelf_number: int
        The ShelfNumber to search for in the database.

        Returns
        -------
            True if the given shelf_number is found in the JSON database file.
            False if the given shelf_number is not found in the JSON database file.
        """
        result = False
        for shelf in self.__db.Shelves.Shelves:
            if shelf_number == shelf.ShelfNumber:
                result = True
                return result
        return result

    def shelf_exists_by_mac_address(self, mac_address: str):
        """
        Returns True if the given MAC-address is found in a Shelf in the database.

        Parameters
        -------
        mac_address: str
        The MAC-address to search for in the database.

        Returns
        -------
        True if the given MAC-address is found in a Shelf in the database.
        False if the given MAC-address is not found in a Shelf in the database.
        """
        result = False
        shelves = self.get_shelf_array().Shelves
        for shelf in shelves:
            if shelf.Mac_Address == mac_address:
                result = True
        return result

    def mac_address_exists(self, mac_address: str) -> bool:
        """
        Returns True if the given MAC-address is found in the database.

        Parameters
        -------
        mac_address : str
        The MAC-address to search for in the database.

        Returns
        -------
        True if the given MAC-address is found in the database.
        False if the given MAC-address is not found in the database.
        """
        result = False
        for esp32 in self.__db.ESP32s.ESP32s:
            if mac_address == esp32.Mac_Address:
                result = True
                return result
        return result

    def position_id_exists(self, shelf_number: int, position_id: int) -> bool:
        """
        Returns True if the given PositionId is found at the given ShelfNumber in the database.

        Parameters
        -------
        shelf_number : int
        The ShelfNumber where the PositionId should be found in the database.
        position_id : int
        The PositionId to search for in the given ShelfNumber.

        Returns
        -------
        True if the given ShelfNumber is found in the database and the Shelf
        stores the given PositionId.
        False if the given ShelfNumber is not found in the database
        or the Shelf does not store the given PositionId.
        """
        result = False
        if not self.shelf_exists(shelf_number):
            log.debug("ShelfNumber was not found!")
            return result
        for shelf in self.__db.Shelves.Shelves:
            if shelf.ShelfNumber == shelf_number:
                for position in shelf.Positions:
                    if position.PositionId == position_id:
                        result = True
                        return result
        return result

    def leds_exists(self, leds: List[int], shelf_number: int) -> bool:
        """
        Returns True if one of the LEDs in the given LED array (List[int]) already exists in one of the
        ShelfPositions of the Shelf with the given ShelfNumber.

        Parameters
        -------
        leds : List[int]
        The LED array (List[int]) to look for in the database. When searching for just one LED
        then a List[int] object has to be given with just one LED (int). It has to be a list, not a single int.
        shelf_number: int
        The ShelfNumber of the Shelf in which to search for the LEDs in the database.

        Returns
        -------
        Returns True if one of the LEDs in the given LED array (List[int]) already exists in one of the
        ShelfPositions of the Shelf with the given ShelfNumber.
        Returns False when no LEDs are found in other ShelfPositions in the database.
        """

        result = False
        if not self.shelf_exists(shelf_number):
            log.debug("ShelfNumber was not found!")
            return result
        positions = self.get_positions_by_shelf_number(shelf_number)
        if positions is None or not positions:
            log.debug("Shelf positions from the shelf "
                      "with the given shelf number is empty or None.")
            return result
        for position in positions:
            for led in leds:
                if led in position.LEDs:
                    log.warning("One of the given LEDs is equal to an existing one in the position "
                                "with the id %d in the Shelf with the number %d",
                                position.PositionId, position.ShelfNumber)
                    result = True
                    return result
        return result

    def leds_exists_exclusive(self, shelf_position: ShelfPosition) -> bool:
        """
        Returns True if one of the LEDs in the LED array of the given ShelfPosition already exists in one of the
        ShelfPositions of the Shelf with the ShelfNumber of the given ShelfPosition excluding the LEDs
        in the given ShelfPosition.

        Parameters
        -------
        shelf_position: ShelfPosition
        ShelfPosition whose LEDs have to be excluded from the search query.

        Returns
        -------
        Returns True if one of the LEDs in the LED array of the given ShelfPosition already exists in one of the
        positions of the shelf with the ShelfNumber of the given Shelf Position excluding the LEDs
        in the given ShelfPosition.
        Returns False if the ShelfNumber or the PositionId doesn't exist or none of the LEDs were found
        in other ShelfPositions in the Shelf with the ShelfNumber of the given ShelfPosition.
        """

        result = False
        if not self.shelf_exists(shelf_position.ShelfNumber):
            log.debug("ShelfNumber was not found!")
            return result
        if not self.position_id_exists(shelf_position.ShelfNumber, shelf_position.PositionId):
            log.debug("Position with the given position_id %d doesn't exist so cannot execute "
                      "method leds_exists_exclusive.", shelf_position.PositionId)
            return result
        positions = self.get_positions_by_shelf_number(shelf_position.ShelfNumber)
        if positions is None or not positions:
            log.debug("Shelf positions from the shelf with "
                      "the given shelf number is empty or None.")
            return result
        for position in positions:
            if position.PositionId == shelf_position.PositionId:
                continue
            for led in shelf_position.LEDs:
                if led in position.LEDs:
                    log.warning("Cannot add ShelfPosition because one of the given LEDs is equal "
                                "to an existing one in the position with the id %d in the Shelf "
                                "with the number %d", position.PositionId, position.ShelfNumber)
                    result = True
                    return result
        return result

    def get_shelf_by_shelf_number(self, shelf_number: int) -> Optional[Shelf]:
        """
        Method to get a Shelf object by its ShelfNumber if found in the database.

        Parameters
        -------
        shelf_number: int
        The ShelfNumber to search for in the database.

        Returns
        -------
        A Shelf object if the given ShelfNumber is found in the database.
        None if the given ShelfNumber is not found in the database.
        """
        result = None
        if not self.shelf_exists(shelf_number):
            log.debug("ShelfNumber was not found!")
            return result
        for shelf in self.__db.Shelves.Shelves:
            if shelf.ShelfNumber == shelf_number:
                result = shelf
                return result
        return result

    def get_shelf_by_mac_address(self, mac_address: str) -> Optional[Shelf]:
        """
        Method to get a Shelf object by its MAC-address if found in the database.

        Parameters
        -------
        mac_address: str
        The MAC-address to search for in the database.

        Returns
        -------
        A Shelf object if the given MAC-address is found in the database.
        None if the given MAC-address is not found in the database.
        """
        result = None
        if not self.shelf_exists_by_mac_address(mac_address):
            log.debug("ShelfNumber was not found!")
            return result
        for shelf in self.__db.Shelves.Shelves:
            if shelf.Mac_Address == mac_address:
                result = shelf
                return result
        return result

    def get_shelf_array(self) -> ShelfArray:
        """
        Method to get the ShelfArray object from the DataManager.
        """
        return self.__db.Shelves

    def get_esp32_array(self) -> ESP32Array:
        """
        Method to get the ESP32Array object from the DataManager.
        """
        return self.__db.ESP32s

    def get_mac_address_by_shelf_number(self, shelf_number: int) -> Optional[str]:
        """
        Method to get a MAC address by the ShelfNumber it was assigned to if found in the database.

        Parameters
        -------
        shelf_number: int
        The ShelfNumber to search for in the database.

        Returns
        -------
        A MAC-address if the given ShelfNumber is found in the database.
        None if the given ShelfNumber is not found in the database.
        """
        result = None
        if not self.shelf_exists(shelf_number):
            log.debug("ShelfNumber was not found!")
            return result
        for shelf in self.__db.Shelves.Shelves:
            if shelf.ShelfNumber == shelf_number:
                result = shelf.Mac_Address
                return result
        return result

    def get_position_by_shelf_number_and_position_id(self, shelf_number: int, position_id: int
                                                     ) -> Optional[ShelfPosition]:
        """
        Method to get a ShelfPosition object by its ShelfNumber and PositionId if found in the database.

        Parameters
        -------
        shelf_number: int
        The ShelfNumber to search for in the database.
        position_id : int
        The PositionId to search for in the database.

        Returns
        -------
        A ShelfPosition object if the given ShelfNumber and PositionId is found in the JSON
        database file.
        None if the given ShelfNumber or the PositionId is not found in the JSON database file.
        """
        result = None
        if not self.shelf_exists(shelf_number):
            log.debug("ShelfNumber was not found!")
            return result
        for position in self.get_shelf_by_shelf_number(shelf_number).Positions:
            if position.PositionId == position_id:
                result = position
                return result
        return result

    def get_positions_by_shelf_number(self, shelf_number: int) -> Optional[List[ShelfPosition]]:
        """
        Method to get a List[ShelfPosition] object by its ShelfNumber if found in the database.

        Parameters
        -------
        shelf_number: int
        The ShelfNumber to search for in the database.

        Returns
        -------
        A List[ShelfPosition] object if the given ShelfNumber is found in the database.
        None if the given ShelfNumber is not found in the database.
        """
        result = None
        if not self.shelf_exists(shelf_number):
            log.debug("ShelfNumber was not found!")
            return result
        result = self.get_shelf_by_shelf_number(shelf_number).Positions

        return result

    def get_leds_by_shelf_number_and_position_id(self, shelf_number: int, position_id: int
                                                 ) -> Optional[List[int]]:
        """
        Method to get a List[int] object representing the LEDs of a ShelfPosition by
        its ShelfNumber and at the given PositionId if found in the database.

        Parameters
        -------
        shelf_number: int
        The ShelfNumber to search for in the database.
        position_id : int
        The PositionId to search for in the database.

        Returns
        -------
        A List[int] object representing the LEDs of a ShelfPosition by
        its ShelfNumber and at the given PositionId if found in the database.
        None if the given ShelfNumber or the PositionId is not found in the database.
        """
        result = None
        if not self.shelf_exists(shelf_number):
            log.debug("ShelfNumber was not found!")
            return result
        if not self.position_id_exists(shelf_number, position_id):
            log.debug("PositionId was not found!")
            return result
        for shelf in self.__db.Shelves.Shelves:
            if shelf.ShelfNumber == shelf_number:
                for position in shelf.Positions:
                    if position.PositionId == position_id:
                        result = position.LEDs
                        return result
        return result

    def get_esp32_by_mac_address(self, mac_address: str) -> Optional[ESP32]:
        """
        Method to get a ESP32 object with the given MAC-address
        if found in the database.

        Parameters
        -------
        mac_address : str
        The MAC address to search for in the database.

        Returns
        -------
        An ESP32 object if the given MAC-address is found in the database.
        None if an ESP32 object with the given MAC-address is not found in the database.
        """
        result = None
        if not self.mac_address_exists(mac_address):
            log.debug("ESP32 was not found because MAC-address was not found!")
            return result
        for esp32 in self.__db.ESP32s.ESP32s:
            if esp32.Mac_Address == mac_address:
                result = esp32
                return result
        return result

    def add_shelf(self, shelf: Shelf) -> bool:
        """
        Method to add a Shelf to the database.

        Parameters
        ---------
        shelf : Shelf
        Shelf to be added.

        Returns
        -------
        True if the shelf could be added to database.
        False if the shelf could not be added to database.
        """
        result = False
        if (shelf is None) or (not isinstance(shelf, Shelf)):
            log.warning("Shelf is None or not a valid instance of Shelf!")
            return result
        if self.shelf_exists(shelf.ShelfNumber):
            log.warning("Cannot add Shelf because there "
                        "is already one with the same ShelfNumber!")
            return result
        if not self.mac_address_exists(shelf.Mac_Address):
            log.debug("Given Mac_Address was not found in the database, so cannot add Shelf. In "
                      "order to add a Shelf the Mac_Address has to exist and its attribute isUsed "
                      "has to be False.")
        esp32 = self.get_esp32_by_mac_address(shelf.Mac_Address)
        if esp32 is None:
            return result
        if esp32.isUsed:
            log.debug("Cannot add Shelf because the ESP32 with the given Mac_Address is being "
                      "used by another shelf.")
            return result
        esp32.isUsed = True
        self.__db.Shelves.Shelves.append(shelf)
        self.save_data()
        result = True
        return result

    def delete_shelf_by_shelf_number(self, shelf_number: int) -> bool:
        """
        Method to delete a Shelf from the database by its ShelfNumber. It removes the Shelf from
        the database after setting the attribute isUsed of its assigned ESP32 to False.

        Parameters
        ---------
        shelf_number : int
        ShelfNumber of the Shelf to be deleted.

        Returns
        -------
        True if the Shelf could be deleted from the database.
        False if the Shelf could not be deleted from the database.
        """
        result = False
        shelf = self.get_shelf_by_shelf_number(shelf_number)
        if shelf is None:
            log.debug("Cannot delete shelf with shelf number %d because it doesn't exist "
                      "in our database.", shelf_number)
            return result
        mac_address = self.get_mac_address_by_shelf_number(shelf_number)
        esp32 = self.get_esp32_by_mac_address(mac_address)
        if mac_address is None or esp32 is None:
            log.debug("There isn't an ESP32 assigned to the Shelf with shelf number %d "
                      "so cannot delete it.", shelf_number)
            return result
        try:
            self.__db.Shelves.Shelves.remove(shelf)
        except ValueError:
            log.warning("Couldn't remove shelf because value is not present (ValueError). The "
                        "given shelf must be exactly like the one in the database that has to be "
                        "deleted.")
            return result
        esp32.isUsed = False
        self.save_data()
        result = True
        return result

    def add_position(self, shelf: Shelf, shelf_position: ShelfPosition) -> bool:
        """
        Method to add a ShelfPosition to a Shelf in the database.

        Parameters
        ---------
        shelf : Shelf
        Shelf to be added.
        shelf_position : ShelfPosition
        Shelf position to be added to the given Shelf.

        Returns
        -------
        True if the shelf position could be added to the shelf in the database.
        False if the shelf position could not be added to the shelf in the database.
        """
        result = False
        if not isinstance(shelf, Shelf):
            log.warning("Shelf is None or not a valid instance of Shelf!")
            return result
        if not isinstance(shelf_position, ShelfPosition):
            log.warning("ShelfPosition is None or not a valid instance of ShelfPosition!")
            return result
        if not self.shelf_exists(shelf.ShelfNumber):
            log.warning("Cannot add ShelfPosition because given Shelf doesn't exist!")
            return result
        if self.position_id_exists(shelf.ShelfNumber, shelf_position.PositionId):
            log.warning("Cannot add ShelfPosition because given PositionId already exists!")
            return result
        if shelf_position.PositionId > 255 or shelf_position.PositionId < 0:
            log.warning("Cannot add ShelfPosition "
                        "because given PositionId is not between 0-255.")
            return result
        if not shelf_position.LEDs or shelf_position.LEDs is None:
            log.warning("Cannot add ShelfPosition because given LEDs is empty or None")
            return result
        if self.leds_exists(shelf_position.LEDs, shelf_position.ShelfNumber):
            log.warning("Warning: Cannot add ShelfPosition because one of the given LEDs is equal "
                        "to an existing one in the position with the id %d in the Shelf with the "
                        "number %d", shelf_position.PositionId, shelf_position.ShelfNumber)
            return result
        shelf_position.ShelfNumber = shelf.ShelfNumber
        shelf.Positions.append(shelf_position)
        self.save_data()
        result = True
        return result

    def update_position(self, shelf: Shelf, shelf_position: ShelfPosition) -> bool:
        """
        Method to update a ShelfPosition from the given Shelf in the database.

        Parameters
        ---------
        shelf : Shelf
        Shelf where the ShelfPosition to be updated has to be stored in.
        shelf_position : ShelfPosition
        ShelfPosition to be updated.

        Returns
        -------
        True if the ShelfPosition could be updated in the Shelf in the database.
        False if the ShelfPosition could not be updated in the Shelf in the database.
        """
        result = False
        if (shelf is None) or (not isinstance(shelf, Shelf)):
            log.warning("Shelf is None or not a valid instance of Shelf!")
            return result
        if (shelf_position is None) or (not isinstance(shelf_position, ShelfPosition)):
            log.warning("ShelfPosition is None or not a valid instance of ShelfPosition!")
            return result
        if not self.shelf_exists(shelf.ShelfNumber):
            log.warning("Cannot add ShelfPosition because given Shelf doesn't exist!")
            return result
        if not self.position_id_exists(shelf.ShelfNumber, shelf_position.PositionId):
            log.warning("Cannot update ShelfPosition because given PositionId doesn't exist "
                        "in our database!")
            return result
        if not shelf_position.LEDs or shelf_position.LEDs is None:
            log.warning("Cannot update ShelfPosition because given LEDs is empty or None")
            return result

        if self.leds_exists_exclusive(shelf_position):
            log.warning("Cannot update ShelfPosition because one of the given LEDs is "
                        "equal to another existing one.")
            return result
        position_to_be_updated = \
            self.get_position_by_shelf_number_and_position_id(shelf.ShelfNumber,
                                                              shelf_position.PositionId)

        position_to_be_updated.ShelfNumber = shelf.ShelfNumber
        position_to_be_updated.LEDs = shelf_position.LEDs
        self.save_data()
        result = True
        return result

    def delete_position(self, shelf: Shelf, shelf_position: ShelfPosition) -> bool:
        """
        Method to delete a ShelfPosition from a Shelf in the database.

        Parameters
        ---------
        shelf : Shelf
        Shelf where the ShelfPosition to be deleted has to be stored in.
        shelf_position : ShelfPosition
        ShelfPosition to be deleted.

        Returns
        -------
        True if the ShelfPosition could be deleted from the Shelf in the database.
        False if the ShelfPosition could not be deleted from the Shelf in the database.
        """
        if (shelf is None) or (not isinstance(shelf, Shelf)):
            log.warning("Shelf is None or not a valid instance of Shelf!")
            return False
        if (shelf_position is None) or (not isinstance(shelf_position, ShelfPosition)):
            log.warning("ShelfPosition is None or not a valid instance of ShelfPosition!")
            return False
        if not self.shelf_exists(shelf.ShelfNumber):
            log.warning("Cannot delete ShelfPosition because "
                        "given Shelf doesn't exist in the database!")
            return False
        if not self.position_id_exists(shelf.ShelfNumber, shelf_position.PositionId):
            log.warning("Cannot delete ShelfPosition because "
                        "given PositionId doesn't exist in the database!")
            return False

        try:
            shelf.Positions.remove(shelf_position)
        except ValueError:
            log.warning("Couldn't remove shelf_position because value is not "
                        "present (ValueError). The given shelf_position must be exactly like "
                        "the one in the database that has to be deleted.")
            return False

        self.save_data()
        return True

    def add_esp32(self, esp32: ESP32) -> bool:
        """
        Method to add an ESP32 to the database.

        Parameters
        --------
        esp32 : ESP32
        ESP32 object to be added to the database.

        Returns
        -------
        True if the ESP32 object could be added to the database.
        False if the ESP32 object not be added to the database.
        """
        if (esp32 is None) or (not isinstance(esp32, ESP32)):
            log.warning("ESP32 cannot be added because it is None or not a valid instance of "
                        "ESP32!")
            return False
        if self.mac_address_exists(esp32.Mac_Address):
            log.warning("Cannot add ESP32 because given Mac_Address already exists!")
            return False
        self.__db.ESP32s.ESP32s.append(esp32)
        self.save_data()
        return True

    def set_all_esp32s_offline(self) -> None:
        esp32s = self.get_esp32_array()
        if esp32s is None or not esp32s.ESP32s:
            log.warning("Couldn't set any ESP32s offline because the ESP32Array object of the DB object is None or "
                        "the List[ESP32] is empty.")
            return
        for esp32 in esp32s.ESP32s:
            esp32.isOnline = False
