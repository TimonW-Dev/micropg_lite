import network   # Handles the wifi connection
import micropg_lite

### To Do: Fill in your wifi connection data and change the server data
ssid = 'wifissid' # replace the string with your wifi ssid
password = 'secret' # replase tge string with your wifi password

# Connect to network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

print("Wifi connected")

conn = micropg_lite.connect(host='127.0.0.1', # replace the string with your server ip-address
                    user='postgres', # replace the string with your user
                    password='123456', # replace the string with your password
                    database='exampledatabase')
cur = conn.cursor()

cur.execute('delete from customers where id=1;')
conn.close()
