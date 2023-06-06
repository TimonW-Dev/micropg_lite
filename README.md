# micropg_lite (PostgreSQL driver for ESP8266)

A MicroPython PostgreSQL database driver made for microchips specifically for ESP8266 and other microchips that are low on RAM.

Try the [micropg](https://github.com/nakagami/micropg) by [
nakagami](https://github.com/nakagami) library first, if you get memory error a when running the micropython script, this micropg_lite library can help.

## Difference between micropg_lite and [micropg](https://github.com/nakagami/micropg)

micropg_lite is a lightweight version based on [micropg](https://github.com/nakagami/micropg) by [
nakagami](https://github.com/nakagami). The only goal of micropg_lite is to read and write data from PostgreSQL databases using as little ram as possible, so that even microchips with little ram can access a PostgreSQL database.

The disadvantage of micropg_lite is that it cannot execute "CREATE DATABASE" or "DROP DATABASE" queries. The SQL queries no longer have escape parameters that the script adds, as they use too much performance. This is especially important to know when writing SQL queries. Another disadvantage is that database information from the server, such as the version or time format, must be set statically. But all this is explained in the "Installation".

## Installation

1. Download the `micropg_lite.py` and the `getServerData.py` file to the local computer.
2. Run the getServerData.py file on your local machine. Enter the server information. The getServerData.py file will then provide you with data that you should cache.

- NOTE: The sendServerData.py script is a slightly modified version of the [micropg](https://github.com/nakagami/micropg) library. This fetches all dynamic data from the PostgreSQL server which must be set statically in the micropg_lite.py file. This is done automatically with the [micropg](https://github.com/nakagami/micropg) library, but is set statically in the micropg_lite library to save performance.

3. At the top of the micropg_lite.py file is a to-do list. Now you have to work through this todo list. Highlight the selected commented line and press CRTL+F, then replace the value assigned to the variable with the value given to you by the getServerData.py file. Then save the script.

4. Copy the customized micropg_lite file to the "/lib" folder on the microcontroller using the Thonny IDE or another program. If there is no "lib" folder in the root directory, you have to create it.

5. Now you should be able to import the library to your microcontroller in a MicroPython file.

````python
import micropg_lite
````

If there are problems, open an issue on this github repository.

## microchip file tree
````
/
├─ example.py
└─ lib/
    └─ micropg_lite.py
````

## Examples
This is just the micropg_lite code. At least one network connection must be established beforehand. 

For more examples see the examples folder. In the examples folder you will also find the database and data that uses this example code. The micropython scripts in the examples directory also make a wifi connection.

### SELECT example:
````python
import micropg_lite

conn = micropg_lite.connect(host='127.0.0.1', # replace the string with your server ip-address
                    user='postgres', # replace the string with your user
                    password='secret', # replace the string with your password
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

cur.execute('INSERT INTO customers (id, firstName, lastName, email) values (%s, %s, %s, %s)', ['5', 'David', 'Wilson', 'david.wilson@example.com'])
conn.close()

````

### DELETE example
```` python
conn = micropg_lite.connect(host='127.0.0.1', # replace the string with your server ip-address
                    user='postgres', # replace the string with your user
                    password='123456', # replace the string with your password
                    database='exampledatabase')
cur = conn.cursor()

cur.execute('delete from customers where id=1;')
conn.close()

````

### UPDATE example
```` python
conn = micropg_lite.connect(host='127.0.0.1', # replace the string with your server ip-address
                    user='postgres', # replace the string with your user
                    password='123456', # replace the string with your password
                    database='exampledatabase')
cur = conn.cursor()

cur.execute('update customers set firstName=\'UpdatedFirstName\' where id=2;')
conn.close()
````

## micropg_lite sql handling
- You have to set some data static. See installation part of this readme
- You have to put ids into ''. See insert example (id)
- Escape parameters are not allways working. You may have to change your queries.
- You can only commit. Rollback is in `micropg_lite` not supported
- You can only execute INSERT, SELECT, UPDATE and DELETE statements
- You can not execute "CREATE DATABASE" or "DROP DATABASE" queries


## Other restrictions and unsupported features
- Supported Authentication METHOD are only 'trust' and 'scram-sha-256'.
- Not support for array data types.
- Not support for prepared statements.