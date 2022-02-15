# Api

Submodule that manages the REST-API for the HttpToMqtt Server.

## **Modules**
The Api submodule uses the following python modules:
* [datetime](https://docs.python.org/3/library/datetime.html)  
* [re](https://docs.python.org/3/library/re.html)  
* [starlette.status](https://pypi.org/project/starlette/)  
* [uvicorn](https://pypi.org/project/uvicorn/)  

## **Classes**

class **Api**(builtins.object)

   ***

**Api**(ip: str, port: int, mqtt, data\_manager)  
   
Main class of the Api submodule.  
   
### Attributes  
***
   
**ip** : str  
    IP address of the host from the HttpToMqtt Server.  
**port** : int  
    Port on which the HttpToMqtt Server is running.  
**mqtt** : Mqtt  
    MQTT module that manages the MQTT communication  
    between the HttpToMqtt Server and ESP32s  
**data\_manager** : DataManager  
    Object representing the data manager  
    that adds, updates, finds and deletes data from the JSON database. 

***
### Methods defined here:  

**\_\_init\_\_**(self, ip: str, port: int, mqtt, data\_manager)

Initialize an Api object which handles the REST-API
***
**run**(self)

Run the REST-API.
   
## **Functions**
 
**color\_string\_to\_byte\_array**(color\_as\_string: str) -> bytearray

Convert color string to a bytearray with three bytes, each one for the RGB respectively.  
If the specified format is not adhered to then None is returned.  
   
**Parameters**  
color\_as\_string : str  
    String containing the RGB values to be converted to a bytearray.  
    Format has to be '#FFFFFF' just containing hex values. Not case-sensitive.  
   
**Returns**  
A bytearray containing the three RGB values.  
If the specified format is not adhered to then None is returned.

   
## **Data**

**List** = typing.List  
**TIMEOUT** = 5  
**Union** = typing.Union  
**log** = <Logger \_\_init\_\_ (WARNING)>
