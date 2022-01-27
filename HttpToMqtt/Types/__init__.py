# pylint: disable=no-name-in-module
from typing import List
from pydantic import BaseModel


class TurnOn(BaseModel):
    """
    Dataclass to turn LEDs on in
    the given Shelf at the given position.
    Post-body for light/turnOn.

    Attributes
    ----------
    ShelfNumber : int
    ShelfNumber of the Shelf on which LEDs should be turned on.
    PositionId : int
    PositionId of the ShelfPosition on which LEDs should be turned on.
    Color : str
    String containing the RGB values with which the LEDs should be turned on.
    The format of the string has to be #FFFFFF.
    """

    ShelfNumber: int
    PositionId: int
    Color: str  # Format: "#FFFFFF"


class TurnOff(BaseModel):
    """
    Dataclass to turn LEDs off in
    the given Shelf at the given position.
    Post-body for light/turnOff.

    Attributes
    ----------
    ShelfNumber : int
    ShelfNumber of the Shelf on which LEDs should be turned off.
    PositionId : int
    PositionId of the ShelfPosition on which LEDs should be turned off.
    """

    ShelfNumber: int
    PositionId: int


class DeletePosition(BaseModel):
    """
    Dataclass to delete a position with the
    PositionId in the Shelf with the corresponding
    ShelfNumber.
    Delete-body for light/deletePosition.

    Attributes
    ----------
    ShelfNumber : int
    ShelfNumber of the Shelf of which a ShelfPosition has to be deleted.
    PositionId : int
    PositionId of the ShelfPosition that has to be deleted.
    """

    ShelfNumber: int
    PositionId: int


class ShelfSelection(BaseModel):
    """
    Dataclass to ensure a ShelfNumber from
    int type was given.
    Post-body for light/turnOffAll.

    Attributes
    ----------
    ShelfNumber : int
    ShelfNumber of the Shelf to be selected.
    """

    ShelfNumber: int


class ShelfSelectionWithColor(BaseModel):
    """
    Dataclass to ensure a ShelfNumber from
    int type was given and a color.
    Post-body for light/turnOnAll.

    Attributes
    ----------
    ShelfNumber : int
    ShelfNumber of the Shelf to be selected.
    Color : str
    String containing the RGB values with which the LEDs should be turned on.
    The format of the string has to be #FFFFFF.
    """

    ShelfNumber: int
    Color: str  # Format: "#FFFFFF"


class SetLED(BaseModel):
    """
    Dataclass to turn a specific LED array on
    independently of a PositionId or the database.
    LEDs will shine with the given color at the ESP32 with the given Mac_Address.
    Post-body for light/setLEDs.

    Attributes
    ----------
    Mac_Address: str
    MAC-Address of the ESP32 on which the LEDs should be set (turned on).
    LEDs: List[int]
    List of integer values representing the LEDs that should be set (turned on).
    Color: str
    String containing the RGB values with which the LEDs should be set (turned on).
    The format of the string has to be #FFFFFF.
    """

    Mac_Address: str
    LEDs: List[int]
    Color: str


class UnsetLED(BaseModel):
    """
    Dataclass to turn a specific LED array off
    independently of a PositionId or the database.
    LEDs will be turned off at the ESP32 with the given Mac_Address.
    Post-body for light/unsetLEDs.

    Attributes
    ----------
    Mac_Address: str
    MAC-Address of the ESP32 on which the LEDs should be unset (turned off).
    LEDs: List[int]
    List of integer values representing the LEDs that should be unset (turned off).
    """

    Mac_Address: str
    LEDs: List[int]


class ResetESP32(BaseModel):
    """
    Dataclass to reset the ESP32 with the specified Mac_Address.
    Post-body for light/resetESP32.

    Attributes
    ----------
    Mac_Address: str
    MAC-Address of the ESP32 that has to be reset.
    """

    Mac_Address: str


class ShelfPosition(BaseModel):
    """
    Dataclass that represent a position
    in a Shelf. It contains the number of the
    Shelf it is in and its unique ID. The LEDs
    int list containing all LEDs of the position
    int the LED stripe.

    Attributes
    ----------
    ShelfNumber : int
    ShelfNumber of the Shelf in which this ShelfPosition is stored.
    PositionId : int
    PositionId of the ShelfPosition that uniquely identifies this position on the Shelf.
    LEDs: List[int]
    List of integer values representing the LEDs that belong to this ShelfPosition.
    These integer values are in the range 0-255 (a byte sized unsigned integer).
    """

    ShelfNumber: int
    PositionId: int
    LEDs: List[int] = []


class Shelf(BaseModel):
    """
    Dataclass that represents a Shelf.
    It has a unique ShelfNumber and the MAC address
    of the ESP32 that has been assigned to this Shelf.
    It contains all the ShelfPosition objects registered in this Shelf.

    Attributes
    ----------
    ShelfNumber : int
    This number uniquely identifies the Shelf.
    Mac_Address: str
    MAC-Address of the ESP32 that has been assigned to this Shelf.
    Positions: List[ShelfPosition]
    List of ShelfPosition objects containing all ShelfPosition objects stored in this Shelf.
    """

    ShelfNumber: int
    Mac_Address: str
    Positions: List[ShelfPosition] = []


class ShelfArray(BaseModel):
    """
    Dataclass that represents a List of Shelf objects.
    This class is needed for the validation while creating the
    DB object.

    Attributes
    ----------
    Shelves: List[Shelf]
    List of Shelf objects contained in the DB object.
    """

    Shelves: List[Shelf] = []


class ESP32(BaseModel):
    """
    Dataclass representing a registered ESP32.
    Its MAC address is stored along with the status flags :
    isUsed and isOnline.
    When isUsed is True this means that this ESP32 has been
    assigned to a Shelf in the database.
    isOnline gives information about the connection status of the ESP32.

    Attributes
    ----------
    Mac_Address: str
    Physical MAC-Address of an ESP32. Preferred format is 'FF:FF:FF:FF:FF:FF'
    isUsed: bool
    When isUsed is True this means that this ESP32 has been
    assigned to a Shelf in the database.
    isOnline: bool
    Information about the connection status of the ESP32.
    """

    Mac_Address: str
    isUsed: bool
    isOnline: bool


class ESP32Array(BaseModel):
    """
    Dataclass that represents a List of ESP32 objects.
    This class is needed for the validation while creating the
    DB object.

    Attributes
    ----------
    ESP32s: List[ESP32]
    List of ESP32 objects contained in the DB object.
    """
    ESP32s: List[ESP32] = []


class ACK(BaseModel):
    """
    Dataclass representing an ACK.
    ACKs are used to ensure that messages were sent to
    ESP32s and that these were able to do the needed operations.
    An ACK has a unique ID that is used to identify it while waiting for it
    on the server side. After it has been received it is removed from the queue.

    Attributes
    ----------
    Mac_Address: str
    MAC-Address of the ESP32 that is sending the ACK.
    ACK_id: int
    ID that uniquely identifies the ACK being sent and received. With this
    ID it is possible to uniquely identify operations performed by the ESP32s.
    """
    Mac_Address: str
    ACK_id: int


class DB(BaseModel):
    """
    Dataclass representing the database managed by the class
    DataManager.
    Here all data concerning the Shelf objects and ESP32 objects is stored
    and can be serialized in order to be stored in a JSON text file.

    Attributes
    ----------
    Shelves: ShelfArray
    ShelfArray containing all Shelf objects. This would be equivalent to a table in
    a SQL database. Every time CRUD-operations are performed on the database they are
    being made on this ShelfArray object.
    ESP32s: ESP32Array
    ESP32Array containing all ESP32 objects. This would be equivalent to a table in
    a SQL database. Every time CRUD-operations are performed on the database they are
    being made on this ESP32Array object.
    """

    Shelves: ShelfArray
    ESP32s: ESP32Array
