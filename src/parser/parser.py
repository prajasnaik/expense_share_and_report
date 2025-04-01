import shlex

class ParserError(Exception):
    """Custom exception for parsing errors."""
    pass

class Parser:
    def __init__(self):
        # Define valid commands and their argument constraints
        self.commands = {
            'help': {'min': 0, 'max': 0},
            'login': {'min': 2, 'max': 2},
            'logout': {'min': 0, 'max': 0},
            'list_users': {'min': 0, 'max': 0},
            'add_user': {'min': 3, 'max': 3},
            'add_category': {'min': 1, 'max': 1},
            'list_categories': {'min': 0, 'max': 0},
            'add_payment_method': {'min': 1, 'max': 1},
            'list_payment_methods': {'min': 0, 'max': 0},
            'add_expense': {'min': 5, 'max': 6},
            'update_expense': {'min': 3, 'max': 3},
            'delete_expense': {'min': 1, 'max': 1},
            'list_expenses': {'min': 0, 'max': None},
            'import_expenses': {'min': 1, 'max': 1},
            'export_csv': {'min': 3, 'max': 3},
            'report': {'min': 1, 'max': None},
        }

    def parse(self, input_str):
        """Parse input into command and arguments."""
        tokens = shlex.split(input_str.strip())
        if not tokens:
            raise ParserError("No command entered.")
        
        command = tokens[0].lower()
        args = tokens[1:]

        if command not in self.commands:
            raise ParserError(f"Invalid command: {command}")

        cmd_info = self.commands[command]
        min_args, max_args = cmd_info['min'], cmd_info['max']
        num_args = len(args)

        if num_args < min_args:
            raise ParserError(f"Not enough arguments for '{command}'. Expected at least {min_args}, got {num_args}.")
        if max_args is not None and num_args > max_args:
            raise ParserError(f"Too many arguments for '{command}'. Expected at most {max_args}, got {num_args}.")

        return command, args

class CommandHandler:
    def __init__(self, db_connection, current_user=None):
        self.db = db_connection
        self.current_user = current_user
        
        # Main command routing
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
            "report": self.handle_report,
        }

        # Subcommands for reports
        self.report_commands = {
            "top_expenses": self.handle_top_expenses,
            "category_spending": self.handle_category_spending,
            "above_average_expenses": self.handle_above_average,
            "monthly_category_spending": self.handle_monthly_category_spending,
            "highest_spender_per_month": self.handle_highest_spender_monthly,
            "frequent_category": self.handle_frequent_category,
            "payment_method_usage": self.handle_payment_method_usage,
            "tag_expenses": self.handle_tag_expenses,
        }

    def execute_command(self, command: str, args: list):
        """Execute the parsed command."""
        if command not in self.command_map:
            raise ValueError(f"Unknown command: {command}")
        return self.command_map[command](args)

    # handler methods for each command


# Example usage
if __name__ == "__main__":
    parser = Parser()
    handler = CommandHandler(db_connection=None)  # DB connection

    # Simulate user input
    user_input = "report top_expenses 5 2023-01-01 2023-12-31"
    
    try:
        command, args = parser.parse(user_input)
        handler.execute_command(command, args)
    except (ParserError, ValueError) as e:
        print(f"Error: {e}")