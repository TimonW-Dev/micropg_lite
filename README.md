# micropg_lite

**Lightweight PostgreSQL database driver for MicroPython...** <br>
...made for ESP8266, ESP32, RP2040 (Raspberry Pi Pico W) and other microcontrollers.

`micropg_lite` is optimized for boards such as the ESP8266, ESP32, and RP2040 (Raspberry Pi Pico W). This README covers the essentials; see the [project wiki](https://github.com/TimonW-Dev/micropg_lite/wiki) for more detailed documentation.

## 📚 Contents

- [About](#-about)
- [Features and comparison](#-features-and-comparison)
- [Installation](#-installation)
- [Examples](#-examples)
- [Limitations](#-limitations)
- [Tutorial](#-tutorial)
- [Support and acknowledgements](#-support-and-acknowledgements)

## ℹ️ About micropg_lite

`micropg_lite` is a lightweight version of [`micropg`](https://github.com/nakagami/micropg). It is designed for MicroPython devices with limited RAM while retaining support for common SQL operations.

If you need to reduce memory usage further, [`micropg_superlite`](https://github.com/TimonW-Dev/micropg_superlite) is based on `micropg_lite` and removes some features to use even less RAM.

### 📊 Features and comparison

Compare the features and measured RAM usage of the drivers to choose the right PostgreSQL library for your MicroPython project.

| Feature | [micropg](https://github.com/nakagami/micropg) | [micropg_lite](https://github.com/TimonW-Dev/micropg_lite) **(this project)** | [micropg_superlite](https://github.com/TimonW-Dev/micropg_superlite) |
|---|---|---|---|
| 💾 RAM usage¹ | 27,552 bytes (26.91 KiB)<br>Reference | 8,336 bytes (8.14 KiB)<br>70% less than `micropg` | 6,928 bytes (6.77 KiB)<br>75% less than `micropg`; 17% less than `micropg_lite` |
| 🔍 `SELECT` | ✅ Supported | ✅ Supported | ✅ Supported |
| ➕ `INSERT` | ✅ Supported | ✅ Supported | ✅ Supported |
| ✏️ `UPDATE` | ✅ Supported | ✅ Supported | ✅ Supported |
| 🗑️ `DELETE` | ✅ Supported | ✅ Supported | ✅ Supported |
| 🔐 Authentication | ✅ SCRAM-SHA-256, MD5 | ⚠️ SCRAM-SHA-256 only | ⚠️ SCRAM-SHA-256 only |
| ⚠️ Detailed error handling | ✅ Full | ⚠️ Reduced | ⚠️ Reduced |
| 🔒 SSL | ✅ Supported | ✅ Supported | ❌ Not supported |
| 💾 Manual commit | ✅ Supported | ✅ Supported | ❌ Not supported (forced autocommit) |
| ↩️ `ROLLBACK` | ✅ Supported | ✅ Supported | ❌ Not supported |
| 🗄️ Create/drop database | ✅ Supported | ✅ Supported | ❌ Not supported |
| 📦 Native `executemany` support | ✅ Supported | ❌ Not supported | ❌ Not supported |
| 📖 Source code readability | ✅ Readable, clear structure | ⚠️ Compact and optimized for RAM | ⚠️ Compact and optimized for RAM |

¹ RAM usage was measured on a Raspberry Pi Pico W running MicroPython firmware 1.29.0. Actual usage may vary depending on the firmware build and measurement conditions.

## 📥 Installation

### Choose a file

We recommend [`micropg_lite.py`](https://github.com/TimonW-Dev/micropg_lite/blob/main/micropg_lite.py). If you want to save a little more RAM, you can use the precompiled [`micropg_lite.mpy`](https://github.com/TimonW-Dev/micropg_lite/blob/main/micropg_lite.mpy) file. For most projects, the `.py` file is sufficient. The `.mpy` file may not be compatible with every MicroPython firmware version and is not as easy to edit or debug.

### Install on your microcontroller

1. Download the [micropg_lite.py](https://github.com/TimonW-Dev/micropg_lite/blob/main/micropg_lite.py) file from this [repository](https://github.com/TimonW-Dev/micropg_lite) to your local computer.
2. Copy it to the `/lib` folder on your microcontroller using Thonny IDE or another file transfer tool. Create the folder if it does not exist.
   - **Thonny tip:** Open **View** in the top bar and enable **Files** to upload files and create folders on the microcontroller.
3. Import the library in your MicroPython script. The import name is the same for both file formats:

```python
import micropg_lite
```

The files on your microcontroller should be arranged like this:

```text
/
|- example.py
|- lib/
    |- micropg_lite.py
```

## 🚀 Examples

Establish a network connection before running `micropg_lite` code. The SELECT example below includes a Wi-Fi connection template; the other examples assume that the connection is already established.

The [`examples/` folder](https://github.com/TimonW-Dev/micropg_lite/tree/main/examples) contains:

- [`docker-postgres-container-setup.sh`](https://github.com/TimonW-Dev/micropg_lite/blob/main/examples/docker-postgres-container-setup.sh), to create an empty PostgreSQL container.
- [`exampleDatabase.sql`](https://github.com/TimonW-Dev/micropg_lite/blob/main/examples/exampleDatabase.sql), the database used by the examples.
- Complete test scripts with WLAN connection templates, plus examples for creating and dropping tables and databases.

### 🔍 SELECT (including Wi-Fi setup)

Replace the Wi-Fi credentials and server details with your own:

```python
import time
import network
import micropg_lite

ssid = 'wifissid'
password = 'secret'

# Connect to the network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    print("Wi-Fi status:", wlan.status())
    time.sleep(1)

print("Wi-Fi connected")

conn = micropg_lite.connect(
    host='127.0.0.1',  # Replace with your server's IP address
    user='postgres',
    password='123456',
    database='exampledatabase'
)
cur = conn.cursor()

cur.execute('select * from customers')
selectresult = cur.fetchall()
conn.close()

# Print the raw data
print(selectresult)

# Print the data as rows
for row in selectresult:
    for value in row:
        print(value, end="\t")
    print()
```

### ➕ INSERT

```python
conn = micropg_lite.connect(
    host='127.0.0.1',  # Replace with your server's IP address
    user='postgres',
    password='123456',
    database='exampledatabase'
)
cur = conn.cursor()

cur.execute(
    'INSERT INTO customers (id, firstName, lastName, email) values (%s, %s, %s, %s)',
    ['5', 'David', 'Wilson', 'david.wilson@example.com']
)
conn.commit()
conn.close()
```

### ✏️ UPDATE

```python
conn = micropg_lite.connect(
    host='127.0.0.1',  # Replace with your server's IP address
    user='postgres',
    password='123456',
    database='exampledatabase'
)
cur = conn.cursor()

cur.execute("update customers set firstName='UpdatedFirstName' where id=2;")
conn.commit()
conn.close()
```

### 🗑️ DELETE

```python
conn = micropg_lite.connect(
    host='127.0.0.1',  # Replace with your server's IP address
    user='postgres',
    password='123456',
    database='exampledatabase'
)
cur = conn.cursor()

cur.execute("delete from customers where id=1;")
conn.commit()
conn.close()
```

## 🎥 Tutorial

Watch the [YouTube tutorial by Fusion Automate](https://youtu.be/MK_N49lRzlQ?si=hnv1a1Ya2w6zy7NJ) on logging sensor data to PostgreSQL with a Raspberry Pi Pico W.

[![Tutorial by Fusion Automate](https://img.youtube.com/vi/MK_N49lRzlQ/0.jpg)](https://youtu.be/MK_N49lRzlQ?si=hnv1a1Ya2w6zy7NJ)

## 💬 Support and acknowledgements

If you encounter a problem, have a question, or would like to suggest an improvement, please [open an issue](https://github.com/TimonW-Dev/micropg_lite/issues). You can also contact me by email using the address linked in [my profile](https://github.com/TimonW-Dev). This is an open-source project maintained on a voluntary basis, so support is provided as time allows.

`micropg_lite` is based on [`micropg`](https://github.com/nakagami/micropg), developed by [nakagami](https://github.com/nakagami). Many thanks for the great work — without `micropg`, `micropg_lite` would not exist!

Released under the MIT License.
