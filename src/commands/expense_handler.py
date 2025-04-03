import sqlite3
from datetime import datetime
from sqlite3.dbapi2 import Connection
from typing import List, Dict, Optional, Union
from src.auth.auth_integration import ExpenseAuthIntegration

class ExpenseManager:
    def __init__(self, db_connection: Connection, auth: ExpenseAuthIntegration):
        self.db = db_connection
        self.auth = auth

    def list_users(self, format_as_table: bool = True) -> Union[List[Dict[str, Union[int, str, bool]]], str]:
        cursor = self.db.cursor()
        cursor.execute("SELECT user_id, username, is_admin FROM users WHERE is_deleted = 0")
        users = cursor.fetchall()
        
        user_list = [{"user_id": user[0], "username": user[1], "is_admin": bool(user[2])} for user in users]
        
        if not format_as_table:
            return user_list
            
        # Format as table
        headers = ['User ID', 'Username', 'Admin']
        formatted_data = [(u["user_id"], u["username"], "Yes" if u["is_admin"] else "No") for u in user_list]
        
        return self._format_tabular_report(
            "User List", 
            headers, 
            formatted_data
        )

    def add_user(self, username: str, password: str, role: int) -> str:
        current_user = self.auth.get_current_user()
        if not current_user or not current_user.get("is_admin"):
            return "Error: Only admins can add users."
        role = role == 1

        return self.auth.register_new_user(username, password, role)


    def add_category(self, category_name: str) -> str:
        current_user = self.auth.get_current_user()
        if not current_user or not current_user.get("is_admin"):
            return "Error: Only admins can add categories."

        cursor = self.db.cursor()
        try:
            cursor.execute(
                "INSERT INTO categories (category_name, user_id) VALUES (?, ?)",
                (category_name, current_user["user_id"]),
            )
            self.db.commit()
            return f"Category '{category_name}' added successfully."
        except sqlite3.IntegrityError:
            return f"Error: Category '{category_name}' already exists."

    def list_categories(self) -> List[str]:
        cursor = self.db.cursor()
        cursor.execute("SELECT category_name FROM categories WHERE is_deleted = 0")
        categories = cursor.fetchall()
        return [category[0] for category in categories]

    def add_payment_method(self, method_name: str) -> str:
        cursor = self.db.cursor()
        try:
            cursor.execute("INSERT INTO payment_methods (name) VALUES (?)", (method_name,))
            self.db.commit()
            return f"Payment method '{method_name}' added successfully."
        except sqlite3.IntegrityError:
            return f"Error: Payment method '{method_name}' already exists."

    def list_payment_methods(self) -> List[str]:
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM payment_methods WHERE is_deleted = 0")
        methods = cursor.fetchall()
        return [method[0] for method in methods]

    def add_expense(self, amount: float, category: str, payment_method: str, date: str, description: Optional[str], tag: str) -> str:
        current_user = self.auth.get_current_user()
        if not current_user:
            return "Error: No user is currently logged in."

        user_id = current_user["user_id"]
        cursor = self.db.cursor()

        try:
            dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt = datetime.strptime(date, "%Y-%m-%d")
                dt = dt.replace(hour=0, minute=0, second=0)
            except ValueError:
                return "Error: Incorrect date format. Expected YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
        date = dt.strftime("%Y-%m-%d %H:%M:%S")

        # Get category_id and payment_method_id
        cursor.execute("SELECT category_id FROM categories WHERE category_name = ? AND is_deleted = 0", (category,))
        category_id = cursor.fetchone()
        if not category_id:
            return f"Error: Category '{category}' does not exist."

        cursor.execute("SELECT payment_method_id FROM payment_methods WHERE name = ? AND is_deleted = 0", (payment_method,))
        payment_method_id = cursor.fetchone()
        if not payment_method_id:
            return f"Error: Payment method '{payment_method}' does not exist."

        try:
            cursor.execute(
                '''
                INSERT INTO expenses (user_id, category_id, payment_method_id, amount, description, expense_date, tag)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (user_id, category_id[0], payment_method_id[0], amount, description, date, tag),
            )
            self.db.commit()
            return "Expense added successfully."
        except sqlite3.IntegrityError as e:
            return f"Failed to add expense: {e}"

    def update_expense(self, expense_id: int, field: str, new_value: Union[str, float]) -> str:
        current_user = self.auth.get_current_user()
        if not current_user:
            return "Error: No user is currently logged in."
    
        user_id = current_user["user_id"]
        cursor = self.db.cursor()
    
        if field == "expense_date":
            try:
                dt = datetime.strptime(new_value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    dt = datetime.strptime(new_value, "%Y-%m-%d")
                    dt = dt.replace(hour=0, minute=0, second=0)
                except ValueError:
                    return "Error: Incorrect date format. Expected YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
            new_value = dt.strftime("%Y-%m-%d %H:%M:%S")

        # Check if the expense belongs to the logged-in user
        cursor.execute("SELECT user_id FROM expenses WHERE expense_id = ? AND is_deleted = 0", (expense_id,))
        expense_owner = cursor.fetchone()
        if not expense_owner or expense_owner[0] != user_id or not self.auth.is_admin():
            return "Error: You can only update your own expenses."
    
        try:
            cursor.execute(f"UPDATE expenses SET {field} = ? WHERE expense_id = ?", (new_value, expense_id))
            self.db.commit()
            return "Expense updated successfully."
        except sqlite3.OperationalError as e:
            return f"Failed to update expense: {e}"
    
    def delete_expense(self, expense_id: int) -> str:
        current_user = self.auth.get_current_user()
        if not current_user:
            return "Error: No user is currently logged in."
    
        user_id = current_user["user_id"]
        cursor = self.db.cursor()
    
        # Check if the expense belongs to the logged-in user
        cursor.execute("SELECT user_id FROM expenses WHERE expense_id = ? AND is_deleted = 0", (expense_id,))
        expense_owner = cursor.fetchone()
        if not expense_owner or expense_owner[0] != user_id or not self.auth.is_admin():
            return "Error: You can only delete your own expenses."
    
        try:
            cursor.execute("UPDATE expenses SET is_deleted = 1 WHERE expense_id = ?", (expense_id,))
            self.db.commit()
            return "Expense deleted successfully."
        except sqlite3.OperationalError as e:
            return f"Failed to delete expense: {e}"

    def list_expenses(self, filters: Optional[Dict[str, Union[str, List[float]]]] = None, format_as_table: bool = True) -> Union[str, List[Dict[str, Union[int, float, str]]]]:
        current_user = self.auth.get_current_user()
        if not current_user:
            return "Error: No user is currently logged in."
    
        user_id = current_user["user_id"]
        is_admin = current_user.get("is_admin", False)
        cursor = self.db.cursor()
    
        # Base query
        query = """
            SELECT 
                e.expense_id, e.amount, e.description, e.tag, e.expense_date,
                c.category_name, p.name as payment_method,
                u.username
            FROM expenses e
            JOIN categories c ON e.category_id = c.category_id
            JOIN payment_methods p ON e.payment_method_id = p.payment_method_id
            JOIN users u ON e.user_id = u.user_id
            WHERE e.is_deleted = 0
        """
        params = []
    
        # Restrict to user's expenses if not admin
        if not is_admin:
            query += " AND e.user_id = ?"
            params.append(user_id)
    
        # Apply filters
        if filters:
            if "category" in filters:
                query += " AND c.category_name = ?"
                params.append(filters["category"])
            if "date" in filters:
                query += " AND e.expense_date = ?"
                params.append(filters["date"])
            if "amount_range" in filters:
                query += " AND e.amount BETWEEN ? AND ?"
                params.extend(filters["amount_range"])
            if "payment_method" in filters:
                query += " AND p.name = ?"
                params.append(filters["payment_method"])
    
        cursor.execute(query, params)
        expenses = cursor.fetchall()
        
        expense_list = [
            {
                "expense_id": expense[0], 
                "amount": expense[1], 
                "description": expense[2], 
                "tag": expense[3], 
                "date": expense[4],
                "category": expense[5],
                "payment_method": expense[6],
                "username": expense[7]
            }
            for expense in expenses
        ]
        
        if not format_as_table:
            return expense_list
            
        # Format as table
        headers = ['ID', 'Date', 'Amount', 'Category', 'Description', 'Tag', 'Payment Method', 'Username']
        formatted_data = [
            (
                e["expense_id"], 
                e["date"], 
                e["amount"],
                e["category"], 
                e["description"] or "-", 
                e["tag"] or "-", 
                e["payment_method"],
                e["username"]
            ) 
            for e in expense_list
        ]
        
        return self._format_tabular_report(
            "Expense List", 
            headers, 
            formatted_data,
            formatters={
                'Amount': lambda x: f"${x:.2f}"
            }
        )

    def export_data(self, table_name: str, file_path: str, delimiter: str) -> str:
        current_user = self.auth.get_current_user()
        if not current_user:
            return "Error: No user is currently logged in."
    
        user_id = current_user["user_id"]
        is_admin = current_user.get("is_admin", False)
    
        cursor = self.db.cursor()
    
        # Restrict normal users to export only their own data
        if not is_admin:
            if table_name != "expenses":
                return "Error: Normal users can only export their own expenses."
            query = """
                SELECT e.expense_id, u.user_id, c.category_name, p.name as payment_method_name, 
                       e.amount, e.expense_date, e.description, e.tag
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                JOIN payment_methods p ON e.payment_method_id = p.payment_method_id
                JOIN users u ON e.user_id = u.user_id
                WHERE e.user_id = ? AND e.is_deleted = 0
            """
            cursor.execute(query, (user_id,))
        else:
            # Admins can export all data
            query = """
                SELECT e.expense_id, u.user_id, c.category_name, p.name as payment_method_name, 
                       e.amount, e.expense_date, e.description, e.tag
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                JOIN payment_methods p ON e.payment_method_id = p.payment_method_id
                JOIN users u ON e.user_id = u.user_id
                WHERE e.is_deleted = 0
            """
            cursor.execute(query)
    
        rows = cursor.fetchall()
    
        # Fetch column headers
        headers = [description[0] for description in cursor.description]
    
        # Write data to the specified file
        with open(file_path, "w") as file:
            # Write headers
            file.write(delimiter.join(headers) + "\n")
            # Write rows
            for row in rows:
                file.write(delimiter.join(map(str, row)) + "\n")
    
        return f"Data exported to {file_path}."

    def _format_tabular_report(self, title, headers, data, formatters=None):
        """
        Format data into a tabular report with consistent styling.
        
        Args:
            title: Report title string
            headers: List of column header strings
            data: List of data rows (tuples or lists)
            formatters: Optional dict mapping column names to formatting functions
            
        Returns:
            Formatted report string
        """
        # Default column widths
        col_widths = {header: len(header) + 2 for header in headers}
        
        # Determine column widths based on data
        for row in data:
            for i, value in enumerate(row):
                header = headers[i]
                # Format the value if a formatter exists
                if formatters and header in formatters:
                    formatted = formatters[header](value)
                else:
                    formatted = str(value)
                col_widths[header] = max(col_widths[header], len(formatted) + 2)
        
        # Create the report
        report = f"{title}\n"
        report += "=" * len(title) + "\n\n"
        
        # Header row
        header_row = ""
        for header in headers:
            header_row += header.ljust(col_widths[header])
        report += header_row + "\n"
        
        # Separator line
        separator = "-" * sum(col_widths.values()) + "\n"
        report += separator
        
        # Data rows
        for row in data:
            data_row = ""
            for i, value in enumerate(row):
                header = headers[i]
                # Format the value if a formatter exists
                if formatters and header in formatters:
                    formatted = formatters[header](value)
                else:
                    formatted = str(value)
                data_row += formatted.ljust(col_widths[header])
            report += data_row + "\n"
        
        return report
