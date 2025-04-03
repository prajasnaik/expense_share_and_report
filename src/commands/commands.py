from src.auth.user_authentication import UserAuthentication
from src.commands.report_handler import ReportHandler
from src.commands.expense_handler import ExpenseManager
import sqlite3

   
class CommandHandler:
    def __init__(self, db_connection, auth):
        self.auth = auth  # Pass the auth instance to check user roles
        self.expense_manager = ExpenseManager(db_connection)
        self.report_handler = ReportHandler(db_connection)
        self.current_user = None
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
            "export_csv": self.handle_export_csv,
            "report" : self.handle_report
        }
        self.admin_only_commands = {
            "add_user",
            "add_category",
            "import_expenses",
            "export_csv",
            "list_users",
            "report"
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
        user = self.auth.verify_user(username, password)
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
        return self.expense_manager.list_users()

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
    
        password_hash = self.auth.hash_password(password)
        return self.expense_manager.add_user(username, password_hash, is_admin)

    def handle_add_category(self, args):
        """Handle adding a new category (admin only)."""
        category_name = args[0]
        current_user = self.auth.get_current_user()
        return self.expense_manager.add_category(category_name, current_user["user_id"])

    def handle_list_categories(self, args):
        """Handle listing categories."""
        current_user = self.auth.get_current_user()
        return self.expense_manager.list_categories(current_user["user_id"])

    def handle_add_payment_method(self, args):
        """Add a new payment method."""
        payment_method_name = args[0]
        return self.expense_manager.add_payment_method(payment_method_name)

    def handle_list_payment_methods(self, args):
        """List all payment methods."""
        return self.expense_manager.list_payment_methods()

    def handle_add_expense(self, args):
        """Add a new expense."""
        user_id, category_id, payment_method_id, amount, description, *optional_date = args
        date = optional_date[0] if optional_date else None
        return self.expense_manager.add_expense(user_id, category_id, payment_method_id, amount, description, date)

    def handle_update_expense(self, args):
        """Update an existing expense."""
        expense_id, field, new_value = args
        return self.expense_manager.update_expense(expense_id, field, new_value)

    def handle_delete_expense(self, args):
        """Delete an expense."""
        expense_id = args[0]
        return self.expense_manager.delete_expense(expense_id)

    def handle_list_expenses(self, args):
        """Handle listing expenses."""
        current_user = self.auth.get_current_user()
        is_admin = self.auth.is_admin(current_user)
        return self.expense_manager.list_expenses(
            user_id=current_user["user_id"], 
            admin=is_admin
        )

    def handle_import_expenses(self, args):
        """Import expenses from a file."""
        file_path = args[0]
        # Implementation for importing expenses from a file
        return f"Expenses imported from {file_path}."

    def handle_export_csv(self, args):
        """Export data to a CSV file."""
        table_name, file_path, delimiter = args
        return self.expense_manager.export_data(table_name, file_path, delimiter)
    
    def handle_report(self, args):
        if len(args) == 0:
            return "Please specify type of report"
        report_type = args[0]
        self.report_handler.report(report_type, args[1:])