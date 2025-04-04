import sqlite3
import os
import sqlite3
import os
import sys
import datetime


# Database file path
DB_PATH = 'database/app.db'
REPORTING_DB_PATH = 'database/reporting.db'

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

    CREATE TABLE IF NOT EXISTS  expenses(
        expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        payment_method_id INTEGER NOT NULL,
        amount FLOAT NOT NULL,
        expense_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        tag TEXT NOT NULL, 
        is_deleted BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (category_id) REFERENCES categories(category_id),
        FOREIGN KEY (payment_method_id) REFERENCES payment_methods(payment_method_id)                      
    );
    ''')
    
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully at {DB_PATH}")

def init_reporting_db():
    """Initialize the reporting database with denormalized schema for analytics"""
    conn = sqlite3.connect(REPORTING_DB_PATH)
    cursor = conn.cursor()
    
    # Create a denormalized expenses table
    cursor.executescript('''
    -- Denormalized expenses table for reporting
    CREATE TABLE IF NOT EXISTS denormalized_expenses (
        expense_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        category_name TEXT NOT NULL,
        payment_method_name TEXT NOT NULL,
        amount FLOAT NOT NULL,
        expense_date TIMESTAMP NOT NULL,
        description TEXT,
        tag TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL
    );
    
    -- Table to track last update time
    CREATE TABLE IF NOT EXISTS sync_metadata (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        last_sync_time TIMESTAMP NOT NULL
    );
    ''')
    
    # Initialize last_sync_time if it doesn't exist
    cursor.execute("SELECT COUNT(*) FROM sync_metadata")
    if cursor.fetchone()[0] == 0:
        # Initialize with a timestamp far in the past to ensure all records are included on first sync
        cursor.execute('''
        INSERT INTO sync_metadata (id, last_sync_time) VALUES (1, '1970-01-01 00:00:00')
        ''')
    
    conn.commit()
    conn.close()
    
    print(f"Reporting database initialized successfully at {REPORTING_DB_PATH}")

def update_reporting_db():
    """Update the reporting database with new/changed records from the main database"""
    # Connect to both databases
    main_conn = sqlite3.connect(DB_PATH)
    main_conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    main_cursor = main_conn.cursor()
    
    reporting_conn = sqlite3.connect(REPORTING_DB_PATH)
    reporting_cursor = reporting_conn.cursor()
    
    # Get the last sync time
    reporting_cursor.execute("SELECT last_sync_time FROM sync_metadata WHERE id = 1")
    last_sync_time = reporting_cursor.fetchone()[0]
    
    # Current time to use as new last_sync_time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Query expenses updated since last sync
    main_cursor.execute('''
    SELECT 
        e.expense_id, 
        u.username,
        c.category_name,
        pm.name as payment_method_name,
        e.amount,
        e.expense_date,
        e.description,
        e.tag,
        e.created_at,
        e.updated_at
    FROM expenses e
    JOIN users u ON e.user_id = u.user_id
    JOIN categories c ON e.category_id = c.category_id
    JOIN payment_methods pm ON e.payment_method_id = pm.payment_method_id
    WHERE e.updated_at > ? AND e.is_deleted = 0
    ''', (last_sync_time,))
    
    updated_expenses = main_cursor.fetchall()
    
    # Update the reporting database
    for expense in updated_expenses:
        # Check if this expense already exists in the reporting database
        reporting_cursor.execute('''
        SELECT COUNT(*) FROM denormalized_expenses WHERE expense_id = ?
        ''', (expense['expense_id'],))
        
        if reporting_cursor.fetchone()[0] > 0:
            # Update existing record
            reporting_cursor.execute('''
            UPDATE denormalized_expenses SET
                username = ?,
                category_name = ?,
                payment_method_name = ?,
                amount = ?,
                expense_date = ?,
                description = ?,
                tag = ?,
                created_at = ?,
                updated_at = ?
            WHERE expense_id = ?
            ''', (
                expense['username'],
                expense['category_name'],
                expense['payment_method_name'],
                expense['amount'],
                expense['expense_date'],
                expense['description'],
                expense['tag'],
                expense['created_at'],
                expense['updated_at'],
                expense['expense_id']
            ))
        else:
            # Insert new record
            reporting_cursor.execute('''
            INSERT INTO denormalized_expenses (
                expense_id, username, category_name, payment_method_name,
                amount, expense_date, description, tag, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                expense['expense_id'],
                expense['username'],
                expense['category_name'],
                expense['payment_method_name'],
                expense['amount'],
                expense['expense_date'],
                expense['description'],
                expense['tag'],
                expense['created_at'],
                expense['updated_at']
            ))
    
    # Handle deleted expenses in main database
    main_cursor.execute('''
    SELECT expense_id FROM expenses 
    WHERE updated_at > ? AND is_deleted = 1
    ''', (last_sync_time,))
    
    deleted_expense_ids = [row[0] for row in main_cursor.fetchall()]
    
    # Delete these expenses from the reporting database
    if deleted_expense_ids:
        placeholders = ','.join(['?'] * len(deleted_expense_ids))
        reporting_cursor.execute(f'''
        DELETE FROM denormalized_expenses 
        WHERE expense_id IN ({placeholders})
        ''', deleted_expense_ids)
    
    # Update the last sync time
    reporting_cursor.execute('''
    UPDATE sync_metadata SET last_sync_time = ? WHERE id = 1
    ''', (current_time,))
    
    # Commit changes and close connections
    reporting_conn.commit()
    reporting_conn.close()
    main_conn.close()
    
    print(f"Reporting database updated successfully at {current_time}")


if __name__ == "__main__":
    init_db()
    init_reporting_db()
    update_reporting_db()