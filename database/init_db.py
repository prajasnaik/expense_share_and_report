import sqlite3
import os
from src.auth.password_hashing import hash_password  

# Database file path
DB_PATH = 'database/app.db'

# Default admin credentials
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"

def init_db():
    # Check if database file exists and remove it to start fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
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

if __name__ == "__main__":
    init_db()