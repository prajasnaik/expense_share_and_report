import sqlite3
from datetime import datetime

class ExpenseManager:
    def __init__(self, db_connection, auth):
        self.db = db_connection
        self.auth = auth

    def add_user(self, username, password, role):
        current_user = self.auth.get_current_user()
        if not current_user or not current_user.get("is_admin"):
            return "Error: Only admins can add users."

        is_admin = role.lower() == "admin"
        password_hash = self.auth.hash_password(password)
        cursor = self.db.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                (username, password_hash, is_admin),
            )
            self.db.commit()
            return f"User '{username}' added successfully."
        except sqlite3.IntegrityError:
            return f"Error: Username '{username}' already exists."

    def add_category(self, category_name):
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

    def list_categories(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT category_name FROM categories WHERE is_deleted = 0")
        categories = cursor.fetchall()
        return [category[0] for category in categories]

    def add_payment_method(self, method_name):
        cursor = self.db.cursor()
        try:
            cursor.execute("INSERT INTO payment_methods (name) VALUES (?)", (method_name,))
            self.db.commit()
            return f"Payment method '{method_name}' added successfully."
        except sqlite3.IntegrityError:
            return f"Error: Payment method '{method_name}' already exists."

    def list_payment_methods(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM payment_methods WHERE is_deleted = 0")
        methods = cursor.fetchall()
        return [method[0] for method in methods]

    def add_expense(self, amount, category, payment_method, date, description, tag):
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

    def update_expense(self, expense_id, field, new_value):
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
    
    def delete_expense(self, expense_id):
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

    def list_expenses(self, filters=None):
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

    def export_data(self, table_name, file_path, delimiter):
        cursor = self.db.cursor()
        cursor.execute(f"SELECT * FROM ?", (table_name))
        rows = cursor.fetchall()
        with open(file_path, "w") as file:
            for row in rows:
                file.write(delimiter.join(map(str, row)) + "\n")
        return f"Data exported to {file_path}."

