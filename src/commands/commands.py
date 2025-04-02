from src.auth.user_authentication import UserAuthentication
import sqlite3

class CommandHandler:
    def __init__(self, db_connection, auth):
        self.db = db_connection
        self.auth = auth  # Pass the auth instance to check user roles
        self.current_user = None  # Track the currently logged-in user
        self.command_map = {
            "help": self.handle_help,
            "login": self.handle_login,
            "logout": self.handle_logout,
            "list_users": self.handle_list_users,
            "add_user": self.handle_add_user,
            "add_category": self.handle_add_category,
            "list_categories": self.handle_list_categories,
            "add_payment_method": self.handle_add_payment_method,
            "list_payment_methods": self.handle_list_payment_methods,
            "add_expense": self.handle_add_expense,
            "update_expense": self.handle_update_expense,
            "delete_expense": self.handle_delete_expense,
            "list_expenses": self.handle_list_expenses,
            "import_expenses": self.handle_import_expenses,
            "export_csv": self.handle_export_csv
        }
        self.admin_only_commands = {
            "add_user",
            "add_category",
            "import_expenses",
            "export_csv",
            "list_users",
        }  # Commands restricted to admins

    def execute_command(self, command, args):
        if command not in self.command_map:
            raise ValueError(f"Unknown command: {command}")

        # Check if the command is admin-only
        if command in self.admin_only_commands:
            current_user = self.auth.get_current_user()
            if not current_user or not self.auth.is_admin(current_user):
                raise ValueError("This command is restricted to admin users.")

        # Execute the command
        return self.command_map[command](args)

    def handle_help(self, args):
        """Display help information."""
        return "Available commands: " + ", ".join(self.command_map.keys())

    def handle_login(self, args):
        """Handle user login."""
        username, password = args
        user_auth = UserAuthentication(self.db)
        user = user_auth.verify_user(username, password)
        if user:
            self.current_user = user
            return f"Login successful. Welcome, {username}!"
        else:
            return "Invalid username or password."

    def handle_logout(self, args):
        """Handle user logout."""
        if self.current_user:
            self.current_user = None
            return "Logout successful."
        else:
            return "No user is currently logged in."

    def handle_list_users(self, args):
        """List all users."""
        conn = self.db
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, is_admin FROM users WHERE is_deleted = 0")
        users = cursor.fetchall()
        return [{"user_id": user[0], "username": user[1], "is_admin": bool(user[2])} for user in users]

    def handle_add_user(self, args):
        """Handle adding a new user (admin only)."""
        current_user = self.auth.get_current_user()
        if not current_user or not self.auth.is_admin(current_user):
            raise ValueError("Only admins can add new users.")
    
        username, password, is_admin = args
        is_admin = bool(int(is_admin))  # Convert to boolean
    
        # Ensure only admins can create another admin
        if is_admin and not self.auth.is_admin(current_user):
            raise ValueError("Only admins can create another admin user.")
    
        cursor = self.db.cursor()
        password_hash = self.auth.hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            (username, password_hash, is_admin),
        )
        self.db.commit()
        return f"User '{username}' added successfully."

    def handle_add_category(self, args):
        """Handle adding a new category (admin only)."""
        category_name = args[0]
        current_user = self.auth.get_current_user()
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO categories (category_name, user_id) VALUES (?, ?)",
            (category_name, current_user["user_id"]),
        )
        self.db.commit()
        return f"Category '{category_name}' added successfully."

    def handle_list_categories(self, args):
        """Handle listing categories."""
        current_user = self.auth.get_current_user()
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT category_name FROM categories WHERE user_id = ? AND is_deleted = 0",
            (current_user["user_id"],),
        )
        categories = cursor.fetchall()
        return [category[0] for category in categories]

    def handle_add_payment_method(self, args):
        """Add a new payment method."""
        payment_method_name = args[0]
        conn = self.db
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO payment_methods (name) VALUES (?)", (payment_method_name,))
            conn.commit()
            return f"Payment method '{payment_method_name}' added successfully."
        except sqlite3.IntegrityError:
            return f"Payment method '{payment_method_name}' already exists."

    def handle_list_payment_methods(self, args):
        """List all payment methods."""
        conn = self.db
        cursor = conn.cursor()
        cursor.execute("SELECT method_id, name FROM payment_methods")
        methods = cursor.fetchall()
        return [{"method_id": method[0], "name": method[1]} for method in methods]

    def handle_add_expense(self, args):
        """Add a new expense."""
        user_id, category_id, payment_method_id, amount, description, *optional_date = args
        date = optional_date[0] if optional_date else None
        conn = self.db
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO expenses (user_id, category_id, payment_method_id, amount, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, category_id, payment_method_id, amount, description, date))
            conn.commit()
            return "Expense added successfully."
        except sqlite3.IntegrityError as e:
            return f"Failed to add expense: {e}"

    def handle_update_expense(self, args):
        """Update an existing expense."""
        expense_id, field, new_value = args
        conn = self.db
        cursor = conn.cursor()
        try:
            cursor.execute(f"UPDATE expenses SET {field} = ? WHERE expense_id = ?", (new_value, expense_id))
            conn.commit()
            return "Expense updated successfully."
        except sqlite3.OperationalError as e:
            return f"Failed to update expense: {e}"

    def handle_delete_expense(self, args):
        """Delete an expense."""
        expense_id = args[0]
        conn = self.db
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE expense_id = ?", (expense_id,))
        conn.commit()
        return "Expense deleted successfully."

    def handle_list_expenses(self, args):
        """Handle listing expenses."""
        current_user = self.auth.get_current_user()
        cursor = self.db.cursor()

        # Admins can view all expenses; regular users can only view their own
        if self.auth.is_admin(current_user):
            cursor.execute(
                """
                SELECT expense_id, amount, description, tag FROM expenses WHERE is_deleted = 0
                """
            )
        else:
            cursor.execute(
                """
                SELECT expense_id, amount, description, tag FROM expenses
                WHERE user_id = ? AND is_deleted = 0
                """,
                (current_user["user_id"],),
            )

        expenses = cursor.fetchall()
        return [
            {"expense_id": expense[0], "amount": expense[1], "description": expense[2], "tag": expense[3]}
            for expense in expenses
        ]

    def handle_import_expenses(self, args):
        """Import expenses from a file."""
        file_path = args[0]
        # Implementation for importing expenses from a file
        return f"Expenses imported from {file_path}."

    def handle_export_csv(self, args):
        """Export data to a CSV file."""
        table_name, file_path, delimiter = args
        conn = self.db
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        with open(file_path, "w") as file:
            for row in rows:
                file.write(delimiter.join(map(str, row)) + "\n")
        return f"Data exported to {file_path}."