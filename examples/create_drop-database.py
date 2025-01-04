import network   # Handles the wifi connection
import micropg_lite
import time

### To Do: Fill in your wifi connection data and change the server data
ssid = 'ssid'
password = 'secret'


### To Do: Fill in your server connection data
db_host = '127.0.0.1'
db_user = 'postgres'
db_password = '123456'
db_database = 'postgres'

# Connect to network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    print("Wifi Status: ", wlan.status())
    time.sleep(1)

print("Wifi connected")

try:
    micropg_lite.create_database(
        host=db_host, user=db_user, password=db_password, database='testDatabase'
    )
    print("CREATE DATABASE ok")
    
    try:
        micropg_lite.drop_database(
            host=db_host, user=db_user, password=db_password, database='testDatabase'
        )
        print("DROP DATABASE ok")

    except Exception:
        print("DROP DATABASE failed")
    
except Exception:
    print("CREATE DATABASE failed")