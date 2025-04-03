import os
import csv
import sqlite3
import argparse
from datetime import datetime
import re
from pathlib import Path

class ExpenseCSVImporter:
    def __init__(self, db_path='database/app.db', current_user_id=None):
        """Initialize the CSV importer with the database path and user ID."""
        self.db_path = db_path
        self.current_user_id = current_user_id
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found at {db_path}")
        
        if not current_user_id:
            raise ValueError("A valid user ID must be provided")
        
        # Define the expected structure for the expenses CSV
        self.expected_columns = {
            'required': ['category_name', 'payment_method_name', 'amount', 'tag'],
            'optional': ['expense_date', 'description']
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
                
                # Validate at least one row of data
                try:
                    first_row = next(reader)
                    if len(first_row) != len(header):
                        return False, "Data row length doesn't match header length"
                except StopIteration:
                    return False, "CSV file has no data rows"
                
                return True, "CSV structure is valid"
                
        except Exception as e:
            return False, f"Error validating CSV: {str(e)}"
    
    def get_category_id(self, conn, category_name):
        """Get the category ID for a given category name, or create a new category if it doesn't exist."""
        cursor = conn.cursor()
        
        # First, check if the category exists for this user
        cursor.execute(
            "SELECT category_id FROM categories WHERE category_name = ? AND user_id = ? AND is_deleted = 0",
            (category_name, self.current_user_id)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
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
                        
                        # Get or create category and payment method
                        category_id = self.get_category_id(conn, row['category_name'])
                        payment_method_id = self.get_payment_method_id(conn, row['payment_method_name'])
                        
                        # Prepare values for insertion
                        expense_data = {
                            'user_id': self.current_user_id,
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
                        if "could not convert string to float" in str(e):
                            print(f"  Amount must be a valid number. Got: '{row.get('amount', '')}'")
                        rows_failed += 1
                    except sqlite3.Error as e:
                        print(f"Database error in row {rows_inserted + rows_failed + 1}: {str(e)}")
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

def import_expenses_for_user(csv_file, user_id, db_path='database/app.db'):
    """Utility function to import expenses for a user from a given CSV file."""
    try:
        importer = ExpenseCSVImporter(db_path=db_path, current_user_id=user_id)
        return importer.import_expenses_csv(csv_file)
    except Exception as e:
        print(f"Error importing expenses: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Import expense data from CSV files.')
    parser.add_argument('csv_file', help='Path to the CSV file to import')
    parser.add_argument('--user-id', '-u', type=int, required=True, help='User ID of the currently authenticated user')
    parser.add_argument('--db', '-d', help='Path to the database file', default='database/app.db')
    
    args = parser.parse_args()
    
    # Validate CSV file exists
    if not os.path.isfile(args.csv_file):
        print(f"Error: CSV file not found at {args.csv_file}")
        return 1
    
    try:
        importer = ExpenseCSVImporter(db_path=args.db, current_user_id=args.user_id)
        success = importer.import_expenses_csv(args.csv_file)
        return 0 if success else 1
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())