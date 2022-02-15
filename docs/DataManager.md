
# DataManager
Submodule that manages the JSON database containing Shelves and ESP32s.
## **Modules**
The DataManager submodule uses the following python modules:
* [datetime](https://docs.python.org/3/library/datetime.html)  

* [json](https://docs.python.org/3/library/json.html)  

   
## **Classes**
   
class **DataManager**(builtins.object)

**DataManager**(path\_to\_json\_file: pathlib.Path)  
   
A class that manages a JSON database that complies to  
the structure of the Class DB in Types/\_\_init\_\_.py.  
   
### Attributes  
***
**\_\_db** : DB  
    Class containing a Types.ShelfArray object and a Types.ESP32Array object that stores all data during runtime and saves it to a JSON file when needed. This DB object is referred to as the "database" in the entire documentation. When talking about the database it's a reference to this DB object.  
**\_\_path\_to\_json\_file** : Path  
    String with the path to the JSON file that holds the database or in which the database has to be stored.  
**\_\_path\_to\_json\_file\_backup** : Path  
    String with the path to the JSON file that holds a backup of the database. 

 
***
### Methods defined here:  

**\_\_init\_\_**(self, path\_to\_json\_file: pathlib.Path)

Constructs an instance of DataManager.  
   
**Parameters**  
**path\_to\_json\_file** : Path  
    Path object containing the path to the JSON file that holds the database.  
   
**Returns**  
A DataManager object when the specified path ends with '.json'.  If the specified path leads to an existing file, this has to comply to  the JSON structure of the Class DB in Types/\_\_init\_\_.py, otherwise an error will occur. If the file in the specified path doesn't exist then the DataManager is initialized with an empty file/database. If the specified path does not end with '.json' then an exception is raised.
***
**add\_esp32**(self, esp32: HttpToMqtt.Types.ESP32) -> `bool`

Method to add an ESP32 to the database.  
   
**Parameters**
**esp32** : ESP32  
ESP32 object to be added to the database.  
   
**Returns** 
`True` if the ESP32 object could be added to the database.  
`False` if the ESP32 object could not be added to the database.
***
**add\_position**(self, shelf: HttpToMqtt.Types.Shelf, shelf\_position: HttpToMqtt.Types.ShelfPosition) -> `bool`

Method to add a ShelfPosition to a Shelf in the database.  
   
**Parameters** 
**shelf** : Shelf  
Shelf to be added.  
**shelf\_position** : ShelfPosition  
Shelf position to be added to the given Shelf.  
   
**Returns**
`True` if the shelf position could be added to the shelf in the database.  
`False` if the shelf position could not be added to the shelf in the database.
***
**add\_shelf**(self, shelf: HttpToMqtt.Types.Shelf) -> `bool`

Method to add a Shelf to the database.  
   
**Parameters** 
**shelf** : Shelf  
Shelf to be added.  
   
**Returns** 
True if the shelf could be added to database.  
`False` if the shelf could not be added to database.
***
**delete\_position**(self, shelf: HttpToMqtt.Types.Shelf, shelf\_position: HttpToMqtt.Types.ShelfPosition) -> `bool`

Method to delete a ShelfPosition from a Shelf in the database.  
   
**Parameters**
**shelf** : Shelf  
Shelf where the ShelfPosition to be deleted has to be stored in.  
**shelf\_position** : ShelfPosition  
ShelfPosition to be deleted.  
   
**Returns**  
`True` if the ShelfPosition could be deleted from the Shelf in the database.  
`False` if the ShelfPosition could not be deleted from the Shelf in the database.
***
**delete\_shelf\_by\_shelf\_number**(self, shelf\_number: int) -> `bool`

Method to delete a Shelf from the database by its ShelfNumber. It removes the Shelf from  
the database after setting the attribute isUsed of its assigned ESP32 to `False`.  
   

**Parameters**
**shelf\_number** : int  
ShelfNumber of the Shelf to be deleted.  
   
**Returns** 
`True` if the Shelf could be deleted from the database.  
`False` if the Shelf could not be deleted from the database.
***
**get\_esp32\_array**(self) -> `HttpToMqtt.Types.ESP32Array`

Method to get the ESP32Array object from the DataManager.
***

**get\_esp32\_by\_mac\_address**(self, mac\_address: str) -> `Optional\[HttpToMqtt.Types.ESP32\]`

Method to get a ESP32 object with the given MAC-address if found in the database.  
   
**Parameters**
**mac\_address** : str  
The MAC address to search for in the database.  
   
**Returns**   
An ESP32 object if the given MAC-address is found in the database. 
`None` if an ESP32 object with the given MAC-address is not found in the database.
***
**get\_leds\_by\_shelf\_number\_and\_position\_id**(self, shelf\_number: int, position\_id: int) -> `Optional\[List\[int\]\]`

Method to get a List\[int\] object representing the LEDs of a ShelfPosition by its ShelfNumber and at the given PositionId if found in the database.  
   
**Parameters**
**shelf\_number**: int  
The ShelfNumber to search for in the database.  
**position\_id** : int  
The PositionId to search for in the database.  

**Returns**
A List\[int\] object representing the LEDs of a ShelfPosition by  its ShelfNumber and at the given PositionId if found in the database.  
`None` if the given ShelfNumber or the PositionId is not found in the database.
***
**get\_mac\_address\_by\_shelf\_number**(self, shelf\_number: int) -> `Optional\[str\]`

Method to get a MAC address by the ShelfNumber it was assigned to if found in the database.  
   

**Parameters**

**shelf\_number**: int  
The ShelfNumber to search for in the database.  
   
**Returns**    
A MAC-address if the given ShelfNumber is found in the database.  
`None` if the given ShelfNumber is not found in the database.
***
**get\_position\_by\_shelf\_number\_and\_position\_id**(self, shelf\_number: int, position\_id: int) -> `Optional\[HttpToMqtt.Types.ShelfPosition\]`

Method to get a ShelfPosition object by its ShelfNumber and PositionId if found in the database.  
   
**Parameters**
**shelf\_number**: int  
The ShelfNumber to search for in the database.  
**position\_id** : int  
The PositionId to search for in the database.  
   
**Returns**
A ShelfPosition object if the given ShelfNumber and PositionId is found in the JSON  
database file.  
`None` if the given ShelfNumber or the PositionId is not found in the JSON database file.
***
**get\_positions\_by\_shelf\_number**(self, shelf\_number: int) -> `Optional\[List\[HttpToMqtt.Types.ShelfPosition\]\]`

Method to get a List\[ShelfPosition\] object by its ShelfNumber if found in the database.  
   
**Parameters**
**shelf\_number**: int  
The ShelfNumber to search for in the database.  
   
**Returns**  
A List\[ShelfPosition\] object if the given ShelfNumber is found in the database.  
`None` if the given ShelfNumber is not found in the database.
***
**get\_shelf\_array**(self) -> `HttpToMqtt.Types.ShelfArray`

Method to get the ShelfArray object from the DataManager.
***

**get\_shelf\_by\_mac\_address**(self, mac\_address: str) -> `Optional\[HttpToMqtt.Types.Shelf\]`

Method to get a Shelf object by its MAC-address if found in the database.  
   
**Parameters**
**mac\_address**: str  
The MAC-address to search for in the database.  
   
**Returns**  
A Shelf object if the given MAC-address is found in the database.  
`None` if the given MAC-address is not found in the database.
***
**get\_shelf\_by\_shelf\_number**(self, shelf\_number: int) -> `Optional\[HttpToMqtt.Types.Shelf\]`

Method to get a Shelf object by its ShelfNumber if found in the database.  
   
**Parameters**
**shelf\_number**: int  
The ShelfNumber to search for in the database.  
   
**Returns**
A Shelf object if the given ShelfNumber is found in the database.  
`None` if the given ShelfNumber is not found in the database.
***
**leds\_exists**(self, leds: List\[int\], shelf\_number: int) -> `bool`

Returns `True` if one of the LEDs in the given LED array (List\[int\]) already exists in one of the ShelfPositions of the Shelf with the given ShelfNumber.  
   
**Parameters**  
**leds** : List\[int\]  
The LED array (List\[int\]) to look for in the database. When searching for just one LED then a List\[int\] object has to be given with just one LED (int). It has to be a list, not a single int.  
**shelf\_number**: int  
The ShelfNumber of the Shelf in which to search for the LEDs in the database.  
   
**Returns**
Returns `True` if one of the LEDs in the given LED array (List\[int\]) already exists in one of the ShelfPositions of the Shelf with the given ShelfNumber.  
Returns `False` when no LEDs are found in other ShelfPositions in the database.
***
**leds\_exists\_exclusive**(self, shelf\_position: HttpToMqtt.Types.ShelfPosition) -> `bool`

Returns `True` if one of the LEDs in the LED array of the given ShelfPosition already exists in one of the ShelfPositions of the Shelf with the ShelfNumber of the given ShelfPosition excluding the LEDs in the given ShelfPosition.  
   
**Parameters**
**shelf\_position**: ShelfPosition  
ShelfPosition whose LEDs have to be excluded from the search query.  
   
**Returns** 
Returns `True` if one of the LEDs in the LED array of the given ShelfPosition already exists in one of the positions of the shelf with the ShelfNumber of the given ShelfPosition excluding the LEDs in the given ShelfPosition.  
Returns `False` if the ShelfNumber or the PositionId doesn't exist or none of the LEDs were found in other ShelfPositions in the Shelf with the ShelfNumber of the given ShelfPosition.
***
**mac\_address\_exists**(self, mac\_address: str) -> bool

Returns `True` if the given MAC-address is found in the database.  
   
**Parameters** 
**mac\_address** : str  
The MAC-address to search for in the database.  
   
**Returns**
True if the given MAC-address is found in the database.  
`False` if the given MAC-address is not found in the database.
***
**position\_id\_exists**(self, shelf\_number: int, position\_id: int) -> `bool`

Returns `True` if the given PositionId is found at the given ShelfNumber in the database.  
   
**Parameters** 
**shelf\_number** : int  
The ShelfNumber where the PositionId should be found in the database.  
**position\_id** : int  
The PositionId to search for in the given ShelfNumber.  
   
**Returns**  
`True` if the given ShelfNumber is found in the database and the Shelf stores the given PositionId.  
`False` if the given ShelfNumber is not found in the database or the Shelf does not store the given PositionId.
***
**save\_backup\_data**(self) -> `None`

Saves a backup of the data stored in the DB object from the DataManager as JSON in a text file.
***
**save\_data**(self) -> `None`
Saves the data stored in the DB object from the DataManager as JSON in a text file.
***
**set\_all\_esp32s\_offline**(self) -> `None`
Set the attribute `isOnline` of every ESP32 object stored in the database to `False`.
***

**shelf\_exists**(self, shelf\_number: int) -> `bool`

Returns `True` if the given ShelfNumber is found in the database.  
   
**Parameters**
**shelf\_number**: int  
The ShelfNumber to search for in the database.  
   
**Returns**
    `True` if the given shelf\_number is found in the JSON database file.  
    `False` if the given shelf\_number is not found in the JSON database file.
***
**shelf\_exists\_by\_mac\_address**(self, mac\_address: str) -> `bool`

Returns `True` if the given MAC-address is found in a Shelf in the database.  
   
**Parameters**
**mac\_address**: str  
The MAC-address to search for in the database.  
   
**Returns**  
`True` if the given MAC-address is found in a Shelf in the database.  
`False` if the given MAC-address is not found in a Shelf in the database.
***
**update\_position**(self, shelf: HttpToMqtt.Types.Shelf, shelf\_position: HttpToMqtt.Types.ShelfPosition) -> `bool`

Method to update a ShelfPosition from the given Shelf in the database.  
   
**Parameters**
**shelf** : Shelf  
Shelf where the ShelfPosition to be updated has to be stored in.  
**shelf\_position** : ShelfPosition  
ShelfPosition to be updated.  
   
**Returns** 
`True` if the ShelfPosition could be updated in the Shelf in the database.  
`False` if the ShelfPosition could not be updated in the Shelf in the database.
***


