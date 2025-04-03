import sqlite3
import os
import sqlite3
import os
import sys
import datetime

from src.auth.password_hashing import hash_password

# Database file path
DB_PATH = 'database/app.db'

# Default admin credentials
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"

def init_db():
    # Check if database file exists and remove it to start fresh
    
    # Connect to database (this will create the file if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript('''
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin BOOLEAN NOT NULL DEFAULT 0,
        is_deleted BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        is_deleted BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
                         
    CREATE TABLE IF NOT EXISTS payment_methods (
        payment_method_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        is_deleted BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS expenses (
        expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        payment_method_id INTEGER NOT NULL,
        amount FLOAT NOT NULL,
        expense_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        tag TEXT NOT NULL, 
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (category_id) REFERENCES categories(category_id),
        FOREIGN KEY (payment_method_id) REFERENCES payment_methods(payment_method_id)                      
    );
    ''')
    
    # Check if an admin user already exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        # Insert default admin user
        cursor.execute('''
        INSERT INTO users (username, password_hash, is_admin)
        VALUES (?, ?, ?)
        ''', (DEFAULT_ADMIN_USERNAME, hash_password(DEFAULT_ADMIN_PASSWORD), True))
        print(f"Default admin user created with username: '{DEFAULT_ADMIN_USERNAME}' and password: '{DEFAULT_ADMIN_PASSWORD}'")
    else:
        print("Admin user already exists. Skipping admin creation.")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully at {DB_PATH}")

def insert_sample_data():
    """Insert sample data into the tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert users
    users = [
        ("john_doe", hash_password("password1"), 1),
        ("jane_smith", hash_password("password2"), 0),
        ("bob_jones", hash_password("password3"), 0)
    ]
    
    for user in users:
        cursor.execute('''
        INSERT INTO users (username, password_hash, is_admin)
        VALUES (?, ?, ?)
        ''', user)
    
    # Insert payment methods
    payment_methods = [
        ("Credit Card",),
        ("Cash",),
        ("UPI",),
        ("Bank Transfer",)
    ]
    
    for pm in payment_methods:
        cursor.execute('''
        INSERT INTO payment_methods (name)
        VALUES (?)
        ''', pm)
    
    # Insert categories
    categories = [
        ("Food", 1),
        ("Transportation", 1),
        ("Entertainment", 1),
        ("Utilities", 2),
        ("Shopping", 2),
        ("Health", 3)
    ]
    
    for category in categories:
        cursor.execute('''
        INSERT INTO categories (category_name, user_id)
        VALUES (?, ?)
        ''', category)
    
    # Insert expenses
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prev_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    older_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    
    expenses = [
        (1, 1, 1, 25.50, current_date, "Lunch", "meal"),
        (1, 2, 2, 15.00, prev_date, "Taxi", "travel"),
        (1, 3, 1, 50.00, older_date, "Movie tickets", "leisure"),
        (2, 4, 3, 100.00, current_date, "Electricity bill", "bills"),
        (2, 5, 1, 75.25, prev_date, "New clothes", "clothes"),
        (3, 6, 4, 200.00, current_date, "Doctor visit", "medical")
    ]
    
    for expense in expenses:
        cursor.execute('''
        INSERT INTO expenses (user_id, category_id, payment_method_id, amount, expense_date, description, tag)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', expense)
    
    conn.commit()
    conn.close()
    
    print("Sample data inserted successfully!")

if __name__ == "__main__":
    init_db()