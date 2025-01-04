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

conn = micropg_lite.connect(host=db_host,
                    user=db_user,
                    password=db_password,
                    database=db_database)
cur = conn.cursor()

cur.execute("SELECT c.firstName || ' ' || c.lastName AS customer_name, c.email, c.birthDate, o.orderDate, o.status, p.name AS product_name, p.price, oi.quantity, cat.name AS category_name, i.lastRestockDate, COALESCE(p.description, 'No description available') AS product_description, CASE WHEN c.loyaltyPoints > 500 THEN 'VIP' WHEN c.loyaltyPoints > 100 THEN 'Regular' ELSE 'New' END AS customer_status, c.birthDate AS customer_birth_date FROM customers c LEFT JOIN orders o ON c.id = o.customerId LEFT JOIN order_items oi ON o.id = oi.orderId LEFT JOIN products p ON oi.productId = p.id LEFT JOIN categories cat ON p.categoryId = cat.id RIGHT JOIN inventory i ON p.id = i.productId WHERE o.orderDate >= '2024-03-20' AND i.quantity > 0 ORDER BY o.orderDate DESC LIMIT 5;")
selectresult = cur.fetchall()
conn.close()

print("\n---\n")

print(selectresult)

expectedresult = "[('Emily* %Brown', 'emily.brown@example.com', '1995-02-28', '2024-03-30 15:30:00', 'Completed', 'Smart Watch', '199.99', 1, 'Smartphones', '2024-03-08', 'Fitness tracking and notifications', 'New', '1995-02-28'), ('Emily* %Brown', 'emily.brown@example.com', '1995-02-28', '2024-03-30 15:30:00', 'Completed', 'External Hard Drive', '89.99', 1, 'Computers', '2024-03-11', '2TB storage capacity', 'New', '1995-02-28'), ('Emma-Hans 0Clark$', 'emma.clark@example.com', '1998-08-08', '2024-03-29 13:20:00', 'Processing', 'Coffee Maker', '79.99', 1, 'Home & Kitchen', '2024-03-09', '12-cup programmable coffee maker', 'New', '1998-08-08'), ('Mich!?l# Lee@LeeTestChar=?{}()', 'michael.lee@example.com', '1987-03-25', '2024-03-28 10:00:00', 'Pending', 'Laptop Pro X', '1299.99', 1, 'Computers', '2024-03-01', 'High-performance laptop with 16GB RAM', 'Regular', '1987-03-25'), ('Jane Smith', 'jane.smith@example.com', '1985-12-03', '2024-03-26 11:15:00', 'Completed', 'Wireless Mouse', '39.99', 1, 'Accessories', '2024-03-12', 'Ergonomic design with long battery life', 'Regular', '1985-12-03')]"

if expectedresult == str(selectresult):
    print("Select ok")
else:
    print("Select failed")

print("\n---\n")

# EXAMPLE: Print data table
for r1 in selectresult:
    for r2 in r1:
        print(r2, end="\t")
    print()