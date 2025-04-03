from src.parser.import_csv import ExpenseCSVImporter
from src.commands.report_handler import ReportHandler
from src.auth.auth_integration import ExpenseAuthIntegration
from src.commands.expense_handler import ExpenseManager
import sqlite3

   
class CommandHandler:
    def __init__(self, db_connection, auth: ExpenseAuthIntegration):
        self.auth = auth  # Pass the auth instance to check user roles
        self.expense_manager = ExpenseManager(db_connection, auth)
        self.report_handler = ReportHandler(db_connection)
        self.expense_importer = ExpenseCSVImporter(current_user_id=auth.get_current_user().get("user_id", 0))
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
            if not current_user or not self.auth.is_admin():
                raise ValueError("This command is restricted to admin users.")

        # Execute the command
        return self.command_map[command](args)

    def handle_help(self, args):
        """Display help information."""
        help_text = "Available commands:\n"
        for command in self.command_map.keys():
            help_text += f"  - {command}\n"
        return help_text

    def handle_login(self, args):
        """Handle user login."""
        if len(args) != 2:
            return "Usage: login <username> <password>"
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
        if len(args) != 3:
            return "Usage: add_user <username> <password> <is_admin (0 or 1)>"
        
        current_user = self.auth.get_current_user()
        if not current_user or not self.auth.is_admin():
            raise ValueError("Only admins can add new users.")
    
        username, password, is_admin = args
        is_admin = bool(int(is_admin))  # Convert to boolean
    
        # Ensure only admins can create another admin
        if is_admin and not self.auth.is_admin():
            raise ValueError("Only admins can create another admin user.")
    
        return self.expense_manager.add_user(username, password, is_admin)

    def handle_add_category(self, args):
        """Handle adding a new category (admin only)."""
        if len(args) != 1:
            return "Usage: add_category <category_name>"
        
        category_name = args[0]
        return self.expense_manager.add_category(category_name)

    def handle_list_categories(self, args):
        """Handle listing categories."""
        return self.expense_manager.list_categories()

    def handle_add_payment_method(self, args):
        """Add a new payment method."""
        if len(args) != 1:
            return "Payment method name must be specified"
        payment_method_name = args[0]
        return self.expense_manager.add_payment_method(payment_method_name)

    def handle_list_payment_methods(self, args):
        """List all payment methods."""
        return self.expense_manager.list_payment_methods()

    def handle_add_expense(self, args):
        """Add a new expense."""
        if len(args) < 5:
            return "Usage: add_expense <amount> <category> <payment_method> <date> <tag> <description (optional)>"
        
        amount, category, payment_method, date, tag, *optional_description = args
        description = optional_description[0] if optional_description else None
        return self.expense_manager.add_expense(amount, category, payment_method, date, description, tag)
    
    def handle_update_expense(self, args):
        """Update an existing expense."""
        if len(args) != 3:
            return "Usage: update_expense <expense_id> <field> <new_value>"

        expense_id, field, new_value = args
        return self.expense_manager.update_expense(expense_id, field, new_value)

    def handle_delete_expense(self, args):
        """Delete an expense."""
        if len(args) != 1:
            return "Usage: delete_expense <expense_id>"

        expense_id = args[0]
        return self.expense_manager.delete_expense(expense_id)

    def handle_list_expenses(self, args):
        """Handle listing expenses with optional filters."""
        filters = {}
    
        # Parse filters from args
        for arg in args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                key = key.strip()
                value = value.strip()
    
                if key in ["category", "date", "payment_method"]:
                    filters[key] = value
                elif key == "amount_range":
                    # Parse amount range as a tuple
                    try:
                        min_amount, max_amount = map(float, value.split("-"))
                        filters[key] = (min_amount, max_amount)
                    except ValueError:
                        return "Error: Invalid amount range format. Use 'amount_range=min-max'."
                else:
                    return f"Error: Unsupported filter '{key}'."
    
        # Call the expense manager with parsed filters
        return self.expense_manager.list_expenses(filters=filters)

    def handle_import_expenses(self, args):
        """Import expenses from a file."""
        if len(args) != 1:
            return "Usage: import_expenses <file_path>"

        file_path = args[0]
        # Implementation for importing expenses from a file
        return f"Expenses imported from {file_path}."

    def handle_export_csv(self, args):
        """Export data to a CSV file."""
        if len(args) != 3:
            return "Usage: export_csv <table_name> <file_path> <delimiter>"

        table_name, file_path, delimiter = args
        return self.expense_manager.export_data(table_name, file_path, delimiter)
    
    def handle_report(self, args):
        if len(args) == 0:
            return "Please specify type of report"
        report_type = args[0]
        return (self.report_handler.report(report_type, args[1:]))