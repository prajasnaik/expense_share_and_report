import os
import csv
import sqlite3
from datetime import datetime
from src.auth.auth_integration import ExpenseAuthIntegration

class ExpenseCSVImporter:
    def __init__(self, auth: ExpenseAuthIntegration, current_user_id=None):
        """Initialize the CSV importer with the database path and user ID."""
        self.auth = auth  # Use the auth object to check user roles
        # Use os.path.join to construct the database path
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current file
        self.db_path = os.path.join(base_dir, '../../database/app.db')  # Construct the relative path to the database
        self.current_user_id = current_user_id
        
        if not current_user_id:
            raise ValueError("A valid user ID must be provided")
        
        # Define the expected structure for the expenses CSV
        self.expected_columns = {
            'required': ['category_name', 'payment_method_name', 'amount', 'tag', 'expense_date'],
            'optional': ['description']
        }
    
    def validate_csv_structure(self, csv_file):
        """Validate that the CSV file structure matches the expected expense structure."""
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # Get the header row
                
                # Check if all required columns are present
                missing_columns = [col for col in self.expected_columns['required'] if col not in header]
                
                if missing_columns:
                    return False, f"Missing required columns: {', '.join(missing_columns)}"
                
                # Check for unknown columns that aren't in required or optional
                all_valid_columns = self.expected_columns['required'] + self.expected_columns['optional']
                unknown_columns = [col for col in header if col not in all_valid_columns]
                
                if unknown_columns:
                    return False, f"Unknown columns found: {', '.join(unknown_columns)}"
                
                return True, "CSV structure is valid"
        except Exception as e:
            return False, f"Error validating CSV: {str(e)}"
    
    def get_category_id(self, conn, category_name):
        """Get the category ID for a given category name, or create a new category if it doesn't exist."""
        cursor = conn.cursor()
        
        # Check if the category exists
        cursor.execute(
            "SELECT category_id FROM categories WHERE category_name = ? AND is_deleted = 0",
            (category_name,)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Only admins can add new categories
        if not self.auth.is_admin():
            raise PermissionError("Only admins can add new categories.")
        
        # If the category doesn't exist, create it
        cursor.execute(
            "INSERT INTO categories (category_name, user_id) VALUES (?, ?)",
            (category_name, self.current_user_id)
        )
        return cursor.lastrowid
    
    def get_payment_method_id(self, conn, payment_method_name):
        """Get the payment method ID for a given payment method name, or create if it doesn't exist."""
        cursor = conn.cursor()
        
        # Check if the payment method exists
        cursor.execute(
            "SELECT payment_method_id FROM payment_methods WHERE name = ? AND is_deleted = 0",
            (payment_method_name,)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Only admins can add new payment methods
        if not self.auth.is_admin():
            raise PermissionError("Only admins can add new payment methods.")
        
        # If the payment method doesn't exist, create it
        cursor.execute(
            "INSERT INTO payment_methods (name) VALUES (?)",
            (payment_method_name,)
        )
        return cursor.lastrowid
    
    def import_expenses_csv(self, csv_file):
        """Import expense data from a CSV file."""
        # First validate the CSV structure
        is_valid, message = self.validate_csv_structure(csv_file)
        if not is_valid:
            print(f"Validation failed: {message}")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Read and insert data
                rows_inserted = 0
                rows_failed = 0
                
                for row in reader:
                    try:
                        # Skip empty rows
                        if not any(row.values()):
                            continue
                        
                        # Check if the current user is an admin
                        is_admin = self.auth.is_admin()
                        
                        # Get or create category and payment method
                        category_id = self.get_category_id(conn, row['category_name'])
                        payment_method_id = self.get_payment_method_id(conn, row['payment_method_name'])
                        
                        # Determine the user_id for the expense
                        if is_admin:
                            # Admins can import expenses for any user
                            if 'user_id' in row and row['user_id']:
                                user_id = int(row['user_id'])
                            else:
                                print(f"Warning: Missing 'user_id' in row {rows_inserted + rows_failed + 1}. Skipping.")
                                rows_failed += 1
                                continue
                        else:
                            # Normal users can only import their own expenses
                            user_id = self.current_user_id
                        
                        # Prepare values for insertion
                        expense_data = {
                            'user_id': user_id,
                            'category_id': category_id,
                            'payment_method_id': payment_method_id,
                            'amount': float(row['amount']),
                            'tag': row['tag'],
                            'description': row.get('description', '')
                        }
                        
                        # Handle expense_date if provided
                        if 'expense_date' in row and row['expense_date']:
                            expense_data['expense_date'] = row['expense_date']
                        
                        # Prepare SQL statement
                        columns = ', '.join(expense_data.keys())
                        placeholders = ', '.join(['?'] * len(expense_data))
                        sql = f"INSERT INTO expenses ({columns}) VALUES ({placeholders})"
                        
                        cursor.execute(sql, list(expense_data.values()))
                        rows_inserted += 1
                        
                    except ValueError as e:
                        print(f"Error in row {rows_inserted + rows_failed + 1}: {str(e)}")
                        rows_failed += 1
                    except sqlite3.Error as e:
                        print(f"Database error in row {rows_inserted + rows_failed + 1}: {str(e)}")
                        rows_failed += 1
                    except PermissionError as e:
                        print(f"Permission error in row {rows_inserted + rows_failed + 1}: {str(e)}")
                        rows_failed += 1
                    except Exception as e:
                        print(f"Error processing row {rows_inserted + rows_failed + 1}: {str(e)}")
                        rows_failed += 1
            
            conn.commit()
            print(f"Successfully imported {rows_inserted} expenses")
            if rows_failed > 0:
                print(f"Failed to import {rows_failed} expenses")
            return rows_inserted > 0
            
        except Exception as e:
            print(f"Error importing CSV: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
            return False
        finally:
            if 'conn' in locals():
                conn.close()