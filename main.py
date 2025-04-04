import sqlite3
import os
from database.init_db import init_db, update_reporting_db, init_reporting_db  # Import the init_db function
from src.auth.auth_integration import ExpenseAuthIntegration
from src.parser.parser import Parser, ParserError
from src.commands.commands import CommandHandler

# Define the correct path to the database file
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "app.db")
REPORTING_DB_PATH =  os.path.join(os.path.dirname(__file__), "database", "reporting.db")

def main():
    # Initialize the database
    init_db()
    init_reporting_db()
    # Connect to the database
    db_connection = sqlite3.connect(DB_PATH)
    reporting_db_connection = sqlite3.connect(REPORTING_DB_PATH)
    # Initialize authentication system
    auth = ExpenseAuthIntegration(db_path=DB_PATH)
    
    # Initialize command handler
    command_handler = CommandHandler(db_connection=db_connection, reporting_db_connection=reporting_db_connection, auth=auth)
    
    # Initialize parser
    parser = Parser()
    
    print("Welcome to the Expense Sharing App!")
    print("Type 'help' for a list of commands or 'exit' to quit.")
    
    while True:
        try:
            # Get user input
            user_input = input("Enter command: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting the application. Goodbye!")
                try: 
                    update_reporting_db()
                except Exception as e:
                    print(f"Falied to save reporting_database: {e}")
                break
            
            # Parse the input
            command, args = parser.parse(user_input)
            
            # Handle the 'help' command
            if command == "help":
                current_user = auth.get_current_user()
                if not current_user:
                    # Basic help for unauthenticated users
                    print("Available commands:")
                    print("- login <username> <password>: Log in to the system.")
                    print("- help: Show this help message.")
                    print("- exit or quit: Exit the application.")
                else:
                    # Delegate to CommandHandler for detailed help
                    print(command_handler.execute_command("help", args))
                continue
            
            # Handle authentication-related commands
            if command in ["login", "logout"]:
                if command == "login":
                    success, message = auth.login(*args)
                    print(message)
                elif command == "logout":
                    success, message = auth.logout()
                    print(message)
                continue
            
            # Ensure user is logged in for other commands
            if not auth.get_current_user():
                print("You must be logged in to execute this command.")
                continue
            
            # Execute the command using CommandHandler
            if command in command_handler.command_map:
                result = command_handler.command_map[command](args)
                print(result)
            else:
                print(f"Unknown command: {command}")
        
        except ParserError as e:
            print(f"Parser Error: {e}")
        except ValueError as e:
            print(f"Command Error: {e}")
        except Exception as e:
            print(f"Unexpected Error: {e}")
        finally:
            # Commit changes to the database
            db_connection.commit()
    
    # Close the database connection
    db_connection.close()

if __name__ == "__main__":
    main()