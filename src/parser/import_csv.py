import os
import csv
import sqlite3
import argparse
from datetime import datetime
import re
from pathlib import Path

class CSVImporter:
    def __init__(self, db_path='database/app.db'):
        """Initialize the CSV importer with the database path."""
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found at {db_path}")
        
        # Define the expected structure for each supported table
        self.table_schemas = {
            'users': {
                'required_columns': ['username', 'password_hash', 'is_admin'],
                'optional_columns': ['is_deleted', 'created_at', 'updated_at'],
                'primary_key': 'user_id'
            },
            'categories': {
                'required_columns': ['category_name', 'user_id'],
                'optional_columns': ['is_deleted', 'created_at', 'updated_at'],
                'primary_key': 'category_id'
            },
            'payment_methods': {
                'required_columns': ['name'],
                'optional_columns': ['is_deleted', 'created_at', 'updated_at'],
                'primary_key': 'payment_method_id'
            },
            'expenses': {
                'required_columns': ['user_id', 'category_id', 'payment_method_id', 'amount', 'tag'],
                'optional_columns': ['expense_date', 'description'],
                'primary_key': 'expense_id'
            }
        }
    
    def validate_csv_structure(self, table_name, csv_file):
        """Validate that the CSV file structure matches the expected table structure."""
        if table_name not in self.table_schemas:
            return False, f"Unsupported table: {table_name}"
        
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # Get the header row
                
                # Check if all required columns are present
                required_columns = self.table_schemas[table_name]['required_columns']
                missing_columns = [col for col in required_columns if col not in header]
                
                if missing_columns:
                    return False, f"Missing required columns: {', '.join(missing_columns)}"
                
                # Check for unknown columns
                all_valid_columns = (
                    required_columns + 
                    self.table_schemas[table_name]['optional_columns'] + 
                    [self.table_schemas[table_name]['primary_key']]
                )
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
    
    def import_csv(self, table_name, csv_file):
        """Import data from a CSV file into the specified table."""
        # First validate the CSV structure
        is_valid, message = self.validate_csv_structure(table_name, csv_file)
        if not is_valid:
            print(f"Validation failed: {message}")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                # Prepare SQL statement
                placeholders = ', '.join(['?'] * len(header))
                column_names = ', '.join(header)
                sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                
                # Read and insert data
                rows_inserted = 0
                for row in reader:
                    # Skip empty rows
                    if not any(row):
                        continue
                    
                    # Convert boolean values
                    processed_row = []
                    for i, value in enumerate(row):
                        # Handle boolean values
                        if header[i] in ['is_admin', 'is_deleted']:
                            if value.lower() in ['true', '1', 'yes', 'y']:
                                processed_row.append(1)
                            elif value.lower() in ['false', '0', 'no', 'n']:
                                processed_row.append(0)
                            else:
                                processed_row.append(value)
                        else:
                            processed_row.append(value)
                    
                    try:
                        cursor.execute(sql, processed_row)
                        rows_inserted += 1
                    except sqlite3.IntegrityError as e:
                        print(f"Integrity error on row {rows_inserted + 1}: {str(e)}")
                        if "UNIQUE constraint failed" in str(e):
                            print(f"Duplicate entry found in row {rows_inserted + 1}. Skipping.")
                        else:
                            print(f"Foreign key constraint failed in row {rows_inserted + 1}. Skipping.")
                    except Exception as e:
                        print(f"Error inserting row {rows_inserted + 1}: {str(e)}")
            
            conn.commit()
            print(f"Successfully imported {rows_inserted} rows into table '{table_name}'")
            return True
            
        except Exception as e:
            print(f"Error importing CSV: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_table_name_from_filename(self, csv_file):
        """Try to determine the table name from the CSV filename."""
        filename = os.path.basename(csv_file)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Try to match with known table names
        for table_name in self.table_schemas.keys():
            # Check for exact match
            if name_without_ext == table_name:
                return table_name
            
            # Check for singular/plural variations
            if name_without_ext + 's' == table_name or name_without_ext == table_name + 's':
                return table_name
        
        return None

def main():
    parser = argparse.ArgumentParser(description='Import CSV files into the application database.')
    parser.add_argument('csv_file', help='Path to the CSV file to import')
    parser.add_argument('--table', '-t', help='Target table name (users, categories, payment_methods, expenses)')
    parser.add_argument('--db', '-d', help='Path to the database file', default='database/app.db')
    
    args = parser.parse_args()
    
    # Validate CSV file exists
    if not os.path.isfile(args.csv_file):
        print(f"Error: CSV file not found at {args.csv_file}")
        return 1
    
    try:
        importer = CSVImporter(db_path=args.db)
        
        # Determine table name
        table_name = args.table
        if not table_name:
            table_name = importer.get_table_name_from_filename(args.csv_file)
            if not table_name:
                print("Error: Could not determine target table from filename.")
                print("Please specify the target table using the --table option.")
                return 1
            print(f"Using table name derived from filename: {table_name}")
        
        # Validate table name
        if table_name not in importer.table_schemas:
            print(f"Error: Invalid table name '{table_name}'")
            print(f"Supported tables: {', '.join(importer.table_schemas.keys())}")
            return 1
        
        # Import the CSV
        success = importer.import_csv(table_name, args.csv_file)
        return 0 if success else 1
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())