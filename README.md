# micropg_lite V3 (The worlds lightest PostgreSQL driver for micropython, )
This README contains the most important things you need to know about micropg_lite. You can find detailed documentation in the [wiki of this repository](https://github.com/TimonW-Dev/micropg_lite/wiki).

## About micropg_lite
### Difference between [micropg_lite](https://github.com/TimonW-Dev/micropg_lite) and [micropg](https://github.com/nakagami/micropg)

[micropg_lite](https://github.com/TimonW-Dev/micropg_lite) is a lightweight version based on [micropg](https://github.com/nakagami/micropg) by [
nakagami](https://github.com/nakagami). If you have RAM/memory issues with [micropg](https://github.com/nakagami/micropg) than this library might solve this issue.

micropg_lite was specially optimised for the ESP8266 microchip to make do with limited RAM. micopg_lite works on any microchip that runs micropyhton.

### Major changes in micropg_lite V3
Those who have already worked with micropg_lite V2 know that the micropg_lite V2 driver has some limitations in terms of functionality. Therefore, micropg_lite V3 was developed from scratch to bring back the functionality that is present in [Nakagami's](https://github.com/nakagami) [micropg](https://github.com/nakagami/micropg). micropg_lite V3 has the advantage that, in addition to having almost no more limitations, it also uses fewer resources than micropg_lite V2.

## Installation

1. Download the `micropg_lite.py` file from this repository to your local computer.

2. Copy the `micropg_lite.py` file to the "/lib" folder on the microcontroller using the Thonny IDE or another program. If there is no "lib" folder in the root directory, you have to create it.

    **Hint** for the Thony IDE:
    
    Open in the top bar the "View" menu and make sure that the entry "Files" has a "✓", if not then click on "Files". Now you can directly download and upload files from your computer to the microcontroller. You also can create folders on the microcontroller.

3. Now you should be able to import the library to your microcontroller in a MicroPython file.

````python
import micropg_lite
````

If there are problems or questions, open an issue on this github repository. We will be happy to help you with your questions.

## microcontroller file tree
````
/
├─ example.py
└─ lib/
    └─ micropg_lite.py
````

## Examples
You need to establish a network connection before executing micropg_lite code. The [SELECT example](#select-example-with-wifi-connection) inclueds the wifi template. All other examples do not include the wifi template.

### examples/ folder
The examples/ folder includes the database sql script which was used to create the database and the used data in all those examples. The examples folder also includes the full scripts used in this readme including the wifi connection template.

### SELECT example with wifi connection:
````python
import network   # Handles the wifi connection
import micropg_lite

### To Do: Fill in your wifi connection data and change the server data
ssid = 'wifissid'
password = 'secret'

# Connect to network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    print("Wifi Status: ", wlan.status())
    time.sleep(1)


print("Wifi connected")

conn = micropg_lite.connect(host='127.0.0.1', # To Do: replace the string with your server ip-address
                    user='postgres', # To Do: replace the string with your user
                    password='123456', # To Do: replace the string with your password
                    database='exampledatabase')
cur = conn.cursor()

cur.execute('select * from customers')
selectresult = cur.fetchall()
conn.close()

# EXAMPLE: Print raw data
print(selectresult)

# EXAMPLE: Print data table
for r1 in selectresult:
    for r2 in r1:
        print(r2, end="\t")
    print()
````

### INSERT example
````python
conn = micropg_lite.connect(host='127.0.0.1', # replace the string with your server ip-address
                    user='postgres', # replace the string with your user
                    password='123456', # replace the string with your password
                    database='exampledatabase')
cur = conn.cursor()

cur.execute('INSERT INTO customers (id, firstName, lastName, email) values (%s, %s, %s, %s)', [5, 'David', 'Wilson', 'david.wilson@example.com'])
conn.commit()
conn.close()

````

### UPDATE example
```` python
conn = micropg_lite.connect(host='127.0.0.1', # replace the string with your server ip-address
                    user='postgres', # replace the string with your user
                    password='123456', # replace the string with your password
                    database='exampledatabase')
cur = conn.cursor()

cur.execute("update customers set firstName='UpdatedFirstName' where id=2;")
conn.commit()
conn.close()
````

### DELETE example
```` python
conn = micropg_lite.connect(host='127.0.0.1', # replace the string with your server ip-address
                    user='postgres', # replace the string with your user
                    password='123456', # replace the string with your password
                    database='exampledatabase')
cur = conn.cursor()

cur.execute("delete from customers where id=1;")
conn.commit()
conn.close()

````

## micropg_lite limitations
- reduced error handling
- no MD5 auth method support
- No native support for the so-called "executemany" function