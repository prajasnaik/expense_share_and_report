import sqlite3

class ExpenseManager:

    """Class to handle all database operations related to expenses and categories"""
    def __init__(self, db_connection):
        self.db = db_connection

    def list_users(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT user_id, username, is_admin FROM users WHERE is_deleted = 0")
        users = cursor.fetchall()
        return [{"user_id": user[0], "username": user[1], "is_admin": bool(user[2])} for user in users]

    def add_user(self, username, password_hash, is_admin):
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            (username, password_hash, is_admin),
        )
        self.db.commit()
        return f"User '{username}' added successfully."

    def add_category(self, category_name, user_id):
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO categories (category_name, user_id) VALUES (?, ?)",
            (category_name, user_id),
        )
        self.db.commit()
        return f"Category '{category_name}' added successfully."

    def list_categories(self, user_id):
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT category_name FROM categories WHERE user_id = ? AND is_deleted = 0",
            (user_id,),
        )
        categories = cursor.fetchall()
        return [category[0] for category in categories]

    def add_payment_method(self, payment_method_name):
        cursor = self.db.cursor()
        try:
            cursor.execute("INSERT INTO payment_methods (name) VALUES (?)", (payment_method_name,))
            self.db.commit()
            return f"Payment method '{payment_method_name}' added successfully."
        except sqlite3.IntegrityError:
            return f"Payment method '{payment_method_name}' already exists."

    def list_payment_methods(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT method_id, name FROM payment_methods")
        methods = cursor.fetchall()
        return [{"method_id": method[0], "name": method[1]} for method in methods]

    def add_expense(self, user_id, category_id, payment_method_id, amount, description, date=None):
        cursor = self.db.cursor()
        try:
            cursor.execute('''
            INSERT INTO expenses (user_id, category_id, payment_method_id, amount, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, category_id, payment_method_id, amount, description, date))
            self.db.commit()
            return "Expense added successfully."
        except sqlite3.IntegrityError as e:
            return f"Failed to add expense: {e}"

    def update_expense(self, expense_id, field, new_value):
        cursor = self.db.cursor()
        try:
            cursor.execute(f"UPDATE expenses SET {field} = ? WHERE expense_id = ?", (new_value, expense_id))
            self.db.commit()
            return "Expense updated successfully."
        except sqlite3.OperationalError as e:
            return f"Failed to update expense: {e}"

    def delete_expense(self, expense_id):
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM expenses WHERE expense_id = ?", (expense_id,))
        self.db.commit()
        return "Expense deleted successfully."

    def list_expenses(self, user_id=None, admin=False):
        cursor = self.db.cursor()
        if admin:
            cursor.execute(
                "SELECT expense_id, amount, description, tag FROM expenses WHERE is_deleted = 0"
            )
        else:
            cursor.execute(
                "SELECT expense_id, amount, description, tag FROM expenses WHERE user_id = ? AND is_deleted = 0",
                (user_id,),
            )
        expenses = cursor.fetchall()
        return [
            {"expense_id": expense[0], "amount": expense[1], "description": expense[2], "tag": expense[3]}
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

