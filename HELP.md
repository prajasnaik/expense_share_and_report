# HELP Documentation

This document provides guidance on using the available commands for the system. Follow the instructions for various functionalities as described below.

---

## Help and Information
- **help**  
    Prints the list of available commands.

---

## User Authentication & Role Management
- **login <username> <password>**  
    Authenticate the user with provided username and password.

- **logout**  
    Ends the current user session.

- **list_users**  
    Displays all users and their roles. *(Admin only)*

---

## User, Category & Payment Method Management
- **add_user <username> <password> <role>**  
    Registers a new user with a specified role. Role options: Admin or User.

- **add_category <category_name>**  
    Adds a new expense category. *(Admin only)*

- **list_categories**  
    Lists all available expense categories.

- **add_payment_method <method_name>**  
    Adds a new payment method.

- **list_payment_methods**  
    Lists all available payment methods.

---

## Expense Management
- **add_expense <amount> <category> <payment_method> <date> <description> <tag>**  
    Adds a new expense with the provided details.

- **update_expense <expense_id> <field> <new_value>**  
    Updates the specified field of an existing expense.

- **delete_expense <expense_id>**  
    Deletes the expense identified by expense_id.

- **list_expenses [filters]**  
    Lists expenses. Optional filters (e.g., category, date, amount range, payment method) can be supplied.
    
    *Note: Implementation of filtering is up to your design.*

---

## Import & Export
- **import_expenses <file_path>**  
    Imports expenses from a CSV file located at file_path.

- **export_csv <file_path>, sort-on <field_name>**  
    Exports expenses to a CSV file located at file_path, sorted by the specified field.

---

## Reports
- **report top_expenses <N> <date range>**  
    Displays the top N highest expenses within a specified date range.

- **report category_spending <category>**  
    Shows total spending for the specified category.

- **report above_average_expenses**  
    Lists expenses that exceed the average spending of their respective category.

- **report monthly_category_spending**  
    Provides a monthly breakdown of total spending per category.

- **report highest_spender_per_month**  
    Identifies the user with the highest spending for each month.

- **report frequent_category**  
    Identifies the most frequently used expense category.

- **report payment_method_usage**  
    Provides a spending breakdown by payment method.

- **report tag_expenses**  
    Lists the number of expenses associated with each tag.

- **update_reporting_database**
    Updates the reporting database with the latest data.
---

For additional information or support, please refer to this document whenever needed.