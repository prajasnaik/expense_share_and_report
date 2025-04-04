# Expense Sharing App

A simple application for expense tracking.

## Overview

This expense sharing app allows users to:
- Create accounts with secure password storage
- Add personal expenses
- Generate expense reports
- Track payment history

## Technology Stack

- Python for backend logic
- SQLite database for data storage
- Password hashing for security
- Report generation with separate reporting db

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Required packages (install using `pip install -r requirements.txt`)

### Installation

1. Clone this repository
2. Install dependencies:
    ```
    pip install -r requirements.txt
    ```
4. Initialize the RSA keys:
    ```bash
    python src/auth/generate_keys.py
    ```
### Running the Application

Launch the application by running:
```
python main.py
```

## Features

### User Management
- Secure user registration with password hashing
- Login/logout functionality
- User profile management

### Expense Tracking
- Add personal expenses

### Reporting
- Generate expense summaries
- View spending by category

## Database Structure

The application uses SQLite with the following core tables:
- Users: Store user information with hashed passwords
- Expenses: Track expense details
- Payments: Record payment history
- Categories with spending categories.

## Security

- All passwords are hashed before storage
- Input validation to prevent SQL injection
- Session management for secure access

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Enhancements

- Employ a separate reporting database alongside the tracking database for more efficient and specialized reporting.
- Introduced a category system to better classify spending.
- Added authorization with admin privileges to manage and monitor system access and configurations.

## Schema

Reporting DB - 

```sqlite
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
```
Expense DB - 

```sqlite
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
```