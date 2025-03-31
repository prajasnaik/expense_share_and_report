# Expense Sharing App

A simple application for tracking and sharing expenses among users.

## Overview

This expense sharing app allows users to:
- Create accounts with secure password storage
- Add personal and shared expenses
- Split costs among multiple users
- Generate expense reports
- Track payment history

## Technology Stack

- Python for backend logic
- SQLite database for data storage
- Password hashing for security
- Report generation

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
3. Initialize the database:
    ```
    python src/init_db.py
    ```

### Running the Application

Launch the application by running:
```
python src/main.py
```

## Features

### User Management
- Secure user registration with password hashing
- Login/logout functionality
- User profile management

### Expense Tracking
- Add personal expenses
- Create shared expenses
- Split bills among multiple users
- Track payment status

### Reporting
- Generate expense summaries
- View spending by category
- Export reports to various formats

## Database Structure

The application uses SQLite with the following core tables:
- Users: Store user information with hashed passwords
- Expenses: Track expense details
- GroupExpenses: Manage shared expenses
- Payments: Record payment history

## Security

- All passwords are hashed before storage
- Input validation to prevent SQL injection
- Session management for secure access

## License

This project is licensed under the MIT License - see the LICENSE file for details.