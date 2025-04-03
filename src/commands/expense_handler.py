import sqlite3
from datetime import datetime
from sqlite3.dbapi2 import Connection
from typing import List, Dict, Optional, Union
from src.auth.auth_integration import ExpenseAuthIntegration

class ExpenseManager:
    def __init__(self, db_connection: Connection, auth: ExpenseAuthIntegration):
        self.db = db_connection
        self.auth = auth

    def list_users(self) -> List[Dict[str, Union[int, str, bool]]]:
        cursor = self.db.cursor()
        cursor.execute("SELECT user_id, username, is_admin FROM users WHERE is_deleted = 0")
        users = cursor.fetchall()
        return [{"user_id": user[0], "username": user[1], "is_admin": bool(user[2])} for user in users]

    def add_user(self, username: str, password: str, role: int) -> str:
        current_user = self.auth.get_current_user()
        if not current_user or not current_user.get("is_admin"):
            return "Error: Only admins can add users."
        
        role = role == 1

        self.auth.register_new_user(username, password, role)

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

    def add_expense(self, amount: float, category: str, payment_method: str, date: str, description: str, tag: Optional[str]) -> str:
        current_user = self.auth.get_current_user()
        if not current_user:
            return "Error: No user is currently logged in."

        user_id = current_user["user_id"]
        cursor = self.db.cursor()

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
    
        # Check if the expense belongs to the logged-in user
        cursor.execute("SELECT user_id FROM expenses WHERE expense_id = ? AND is_deleted = 0", (expense_id,))
        expense_owner = cursor.fetchone()
        if not expense_owner or expense_owner[0] != user_id:
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
        if not expense_owner or expense_owner[0] != user_id:
            return "Error: You can only delete your own expenses."
    
        try:
            cursor.execute("UPDATE expenses SET is_deleted = 1 WHERE expense_id = ?", (expense_id,))
            self.db.commit()
            return "Expense deleted successfully."
        except sqlite3.OperationalError as e:
            return f"Failed to delete expense: {e}"

    def list_expenses(self, filters: Optional[Dict[str, Union[str, List[float]]]] = None) -> Union[str, List[Dict[str, Union[int, float, str]]]]:
        current_user = self.auth.get_current_user()
        if not current_user:
            return "Error: No user is currently logged in."
    
        user_id = current_user["user_id"]
        is_admin = current_user.get("is_admin", False)
        cursor = self.db.cursor()
    
        # Base query
        query = "SELECT expense_id, amount, description, tag, expense_date FROM expenses WHERE is_deleted = 0"
        params = []
    
        # Restrict to user's expenses if not admin
        if not is_admin:
            query += " AND user_id = ?"
            params.append(user_id)
    
        # Apply filters
        if filters:
            if "category" in filters:
                query += " AND category_id = (SELECT category_id FROM categories WHERE category_name = ?)"
                params.append(filters["category"])
            if "date" in filters:
                query += " AND expense_date = ?"
                params.append(filters["date"])
            if "amount_range" in filters:
                query += " AND amount BETWEEN ? AND ?"
                params.extend(filters["amount_range"])
            if "payment_method" in filters:
                query += " AND payment_method_id = (SELECT payment_method_id FROM payment_methods WHERE name = ?)"
                params.append(filters["payment_method"])
    
        cursor.execute(query, params)
        expenses = cursor.fetchall()
        return [
            {"expense_id": expense[0], "amount": expense[1], "description": expense[2], "tag": expense[3], "date": expense[4]}
            for expense in expenses
        ]

    def export_data(self, table_name: str, file_path: str, delimiter: str) -> str:
        cursor = self.db.cursor()
        cursor.execute(f"SELECT * FROM ?", (table_name,))
        rows = cursor.fetchall()
        with open(file_path, "w") as file:
            for row in rows:
                file.write(delimiter.join(map(str, row)) + "\n")
        return f"Data exported to {file_path}."
