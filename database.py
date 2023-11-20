import sqlite3

connection = sqlite3.connect('braketaDB.db')
cursor = connection.cursor()

cursor.execute('''
-- Create table "Customers"
CREATE TABLE IF NOT EXISTS Customers (
    id INTEGER PRIMARY KEY,
    full_name TEXT,
    phone TEXT
);
''')

cursor.execute('''
-- Create table "Managers"
CREATE TABLE IF NOT EXISTS Managers (
    id INTEGER PRIMARY KEY,
    full_name TEXT
);
''')

cursor.execute('''
-- Create table "Statuses"
CREATE TABLE IF NOT EXISTS Statuses (
    id INTEGER PRIMARY KEY,
    name TEXT
);
''')

cursor.execute('''
-- Create table "Items"
CREATE TABLE IF NOT EXISTS Items (
    id INTEGER PRIMARY KEY,
    name TEXT
);
''')

cursor.execute('''
-- Create table "Orders"
CREATE TABLE IF NOT EXISTS Orders (
    id INTEGER PRIMARY KEY,
    name TEXT,
    status_id INTEGER,
    order_date TEXT,
    planned_delivery_date TEXT,
    manager_id INTEGER,
    customer_id INTEGER,
    FOREIGN KEY (status_id) REFERENCES Statuses(id),
    FOREIGN KEY (manager_id) REFERENCES Managers(id),
    FOREIGN KEY (customer_id) REFERENCES Customers(id)
);
''')

cursor.execute('''
-- Create table "OrderItems"
CREATE TABLE IF NOT EXISTS OrderItems (
    id INTEGER PRIMARY KEY,
    order_id INTEGER,
    item_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY (order_id) REFERENCES Orders(id),
    FOREIGN KEY (item_id) REFERENCES Items(id)
);
''')

connection.commit()
connection.close()