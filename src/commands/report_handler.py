import sqlite3
import time

class ReportHandler:
    """
    Handles the generation of expense reports from the expense tracking database.
    Provides multiple report types with consistent formatting and error handling.
    """
    
    def __init__(self, db_connection):
        """Initialize with a database connection"""
        self.db = db_connection

    def report_top_N_expenses(self, n: int, date_range: str):
        """
        Generate a report of the top N expenses by amount within a date range.
        
        Args:
            n: Number of top expenses to show
            date_range: Date range in format 'YYYY/MM/DD - YYYY/MM/DD' or 'YYYY - YYYY'
        
        Returns:
            Formatted report string
        """
        try:
            # Parse the provided date range
            parsed_dates = self.parse_date_range(date_range)
            if isinstance(parsed_dates, str):  # Error message returned
                return parsed_dates
                
            start_date, end_date = parsed_dates
            
            # Execute query with parameters
            results = self._execute_query(
                """
                SELECT e.expense_id, e.expense_date, e.amount, e.description, 
                       c.category_name, u.username, p.name
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                JOIN users u ON u.user_id = e.user_id
                JOIN payment_methods p ON p.payment_method_id = e.payment_method_id 
                WHERE e.expense_date BETWEEN ? AND ?
                ORDER BY e.amount DESC
                LIMIT ?
                """, 
                (start_date, end_date, n)
            )
            
            if not results:
                return f"No expenses found between {start_date} and {end_date}"
            
            # Format the results
            headers = ['ID', 'Date', 'Amount', 'Category', 'Description']
            data = [(row[0], row[1], row[2], row[4], row[3]) for row in results]
            
            return self._format_tabular_report(
                f"Top {n} Expenses from {start_date} to {end_date}", 
                headers, 
                data,
                formatters={'Amount': lambda x: f"${x:.2f}"}
            )
        
        except Exception as e:
            return self._format_error("generating top expenses report", e)

    def report_category_spending(self, category_name: str, date_range: str = None):
        """
        Generate a report of total spending for a specific category.
        
        Args:
            category_name: The name of the category to report on
            date_range: Optional date range in standard format
            
        Returns:
            Formatted report string
        """
        try:
            # Get date range (default or specified)
            date_range_tuple = self._get_date_range(date_range)
            if isinstance(date_range_tuple, str):  # Error message returned
                return date_range_tuple
                
            start_date, end_date = date_range_tuple
            
            # Execute query with parameters
            results = self._execute_query(
                """
                SELECT SUM(e.amount) as total_spending, c.category_name
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                WHERE c.category_name = ? AND e.expense_date BETWEEN ? AND ?
                GROUP BY c.category_name
                """,
                (category_name, start_date, end_date)
            )
            
            if not results or results[0][0] is None:
                return f"No spending found for category '{category_name}' in the specified date range."
            
            # Create simple report
            report = f"Spending for Category: '{category_name}'\n"
            report += "=" * len(report) + "\n\n"
            report += f"Total amount spent: ${results[0][0]:.2f}\n"
            report += f"Time period: {start_date} to {end_date}\n"
            
            return report
            
        except Exception as e:
            return self._format_error("generating category spending report", e)

    def report_above_average_expenses(self, date_range: str = None):
        """
        Generate a report of expenses that exceed their category's average amount.
        
        Args:
            date_range: Optional date range in standard format
            
        Returns:
            Formatted report string
        """
        try:
            # Get date range (default or specified)
            date_range_tuple = self._get_date_range(date_range)
            if isinstance(date_range_tuple, str):  # Error message returned
                return date_range_tuple
                
            start_date, end_date = date_range_tuple
            
            # Execute query with parameters - find expenses above category average
            results = self._execute_query(
                """
                SELECT e.* 
                FROM expenses e
                JOIN (
                    SELECT c.category_id, AVG(amount) as average 
                    FROM expenses e
                    JOIN categories c ON e.category_id = c.category_id
                    GROUP BY c.category_id
                ) av ON e.category_id = av.category_id
                WHERE e.amount > av.average AND e.expense_date BETWEEN ? AND ?
                ORDER BY (e.amount / av.average) DESC
                """,
                (start_date, end_date)
            )
            
            if not results:
                return "No expenses above their category average found in the specified date range."
            
            # Calculate percentage above average for each result
            formatted_data = []
            for row in results:
                expense_id, date, amount, description, category, category_avg = row
                percent_above = ((amount - category_avg) / category_avg) * 100
                formatted_data.append((
                    expense_id, date, amount, category, description, 
                    category_avg, f"{percent_above:.1f}%"
                ))
            
            headers = ['ID', 'Date', 'Amount', 'Category', 'Description', 'Category Avg', '% Above']
            
            return self._format_tabular_report(
                "Expenses Above Category Average", 
                headers, 
                formatted_data,
                formatters={
                    'Amount': lambda x: f"${x:.2f}",
                    'Category Avg': lambda x: f"${x:.2f}"
                }
            )
            
        except Exception as e:
            return self._format_error("generating above average expenses report", e)

    def report_monthly_category_spending(self, year=None):
        """
        Generate a report of spending by category for each month of a year.
        
        Args:
            year: The year to report on (defaults to current year)
            
        Returns:
            Formatted report string
        """
        try:
            # Default to current year if not specified
            if year is None:
                year = time.localtime().tm_year
                
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            
            # Get monthly spending by category
            results = self._execute_query(
                """
                SELECT 
                    strftime('%m', e.expense_date) as month_num,
                    c.category_name,
                    SUM(e.amount) as total
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                WHERE e.expense_date BETWEEN ? AND ?
                GROUP BY month_num, c.category_name
                ORDER BY month_num, c.category_name
                """,
                (start_date, end_date)
            )
            
            if not results:
                return f"No spending data found for year {year}."
            
            # Process results into a structured format for display
            return self._format_monthly_category_report(results, year)
            
        except Exception as e:
            return self._format_error("generating monthly category spending report", e)

    def report_highest_spender_per_month(self, year=None):
        """
        Generate a report showing the user with highest spending for each month.
        
        Args:
            year: The year to report on (defaults to current year)
            
        Returns:
            Formatted report string
        """
        try:
            # Default to current year if not specified
            if year is None:
                year = time.localtime().tm_year
                
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            
            # Get spending by user per month
            monthly_spending = self._execute_query(
                """
                SELECT 
                    strftime('%m', e.expense_date) as month_num,
                    u.username,
                    SUM(e.amount) as total_spent
                FROM expenses e
                JOIN users u ON e.user_id = u.user_id
                WHERE e.expense_date BETWEEN ? AND ?
                GROUP BY month_num, u.username
                ORDER BY month_num, total_spent DESC
                """,
                (start_date, end_date)
            )
            
            if not monthly_spending:
                return f"No spending data found for year {year}."
            
            # Find highest spender for each month
            highest_spenders = self._get_highest_spenders_by_month(monthly_spending)
            
            # Format the results
            return self._format_highest_spenders_report(highest_spenders, year)
            
        except Exception as e:
            return self._format_error("generating highest spender report", e)

    def report_frequent_category(self, date_range: str = None):
        """
        Generate a report showing categories by usage frequency.
        
        Args:
            date_range: Optional date range in standard format
            
        Returns:
            Formatted report string
        """
        try:
            # Get date range (default or specified)
            date_range_tuple = self._get_date_range(date_range)
            if isinstance(date_range_tuple, str):  # Error message returned
                return date_range_tuple
                
            start_date, end_date = date_range_tuple
            
            # Get category usage statistics
            results = self._execute_query(
                """
                SELECT 
                    c.category_name,
                    COUNT(e.expense_id) as usage_count,
                    SUM(e.amount) as total_spent,
                    AVG(e.amount) as avg_transaction
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                WHERE e.expense_date BETWEEN ? AND ?
                GROUP BY c.category_name
                ORDER BY usage_count DESC
                """,
                (start_date, end_date)
            )
            
            if not results:
                return "No category usage data found in the specified date range."
            
            # Format the results
            headers = ['Category', 'Usage Count', 'Total Spent', 'Avg Transaction']
            
            return self._format_tabular_report(
                "Category Usage Frequency", 
                headers, 
                results,
                formatters={
                    'Total Spent': lambda x: f"${x:.2f}",
                    'Avg Transaction': lambda x: f"${x:.2f}"
                }
            )
            
        except Exception as e:
            return self._format_error("generating category frequency report", e)

    def report_payment_method_usage(self, date_range: str = None):
        """
        Generate a report showing spending breakdown by payment method.
        
        Args:
            date_range: Optional date range in standard format
            
        Returns:
            Formatted report string
        """
        try:
            # Get date range (default or specified)
            date_range_tuple = self._get_date_range(date_range)
            if isinstance(date_range_tuple, str):  # Error message returned
                return date_range_tuple
                
            start_date, end_date = date_range_tuple
            
            # Get payment method usage
            payment_methods = self._execute_query(
                """
                SELECT 
                    p.name as payment_method,
                    COUNT(e.expense_id) as usage_count,
                    SUM(e.amount) as total_spent
                FROM expenses e
                JOIN payment_methods p ON e.payment_method_id = p.payment_method_id
                WHERE e.expense_date BETWEEN ? AND ?
                GROUP BY p.name
                ORDER BY total_spent DESC
                """,
                (start_date, end_date)
            )
            
            if not payment_methods:
                return "No payment method usage data found in the specified date range."
            
            # Get total spending for percentage calculation
            total_spending_result = self._execute_query(
                "SELECT SUM(amount) FROM expenses WHERE expense_date BETWEEN ? AND ?",
                (start_date, end_date)
            )
            total_spent = total_spending_result[0][0] if total_spending_result and total_spending_result[0][0] else 0
            
            # Calculate percentages
            formatted_data = []
            for method, count, amount in payment_methods:
                percentage = (amount / total_spent * 100) if total_spent > 0 else 0
                formatted_data.append((method, count, amount, percentage))
            
            headers = ['Payment Method', 'Usage Count', 'Total Spent', '% of Spending']
            
            return self._format_tabular_report(
                "Payment Method Usage Breakdown", 
                headers, 
                formatted_data,
                formatters={
                    'Total Spent': lambda x: f"${x:.2f}",
                    '% of Spending': lambda x: f"{x:.2f}%"
                }
            )
            
        except Exception as e:
            return self._format_error("generating payment method usage report", e)

    def report_tag_expenses(self, date_range: str = None):
        """
        Generate a report showing expense statistics by tag.
        
        Args:
            date_range: Optional date range in standard format
            
        Returns:
            Formatted report string
        """
        try:
            # Get date range (default or specified)
            date_range_tuple = self._get_date_range(date_range)
            if isinstance(date_range_tuple, str):  # Error message returned
                return date_range_tuple
                
            start_date, end_date = date_range_tuple
            
            # Get tag statistics
            results = self._execute_query(
                """
                SELECT 
                    e.tag,
                    COUNT(e.expense_id) as expense_count,
                    SUM(e.amount) as total_spent,
                    AVG(e.amount) as avg_amount
                FROM expenses e
                WHERE e.expense_date BETWEEN ? AND ?
                GROUP BY e.tag
                ORDER BY expense_count DESC
                """,
                (start_date, end_date)
            )
            
            if not results:
                return "No tag data found in the specified date range."
            
            # Format the results
            headers = ['Tag', '# of Expenses', 'Total Spent', 'Avg Amount']
            
            return self._format_tabular_report(
                "Expenses by Tag", 
                headers, 
                results,
                formatters={
                    'Total Spent': lambda x: f"${x:.2f}",
                    'Avg Amount': lambda x: f"${x:.2f}"
                }
            )
            
        except Exception as e:
            return self._format_error("generating tag expenses report", e)

    # Helper methods for query execution and result formatting
    
    def _execute_query(self, query, parameters=()):
        """
        Execute a parameterized SQL query and return the results.
        
        Args:
            query: SQL query string with ? placeholders
            parameters: Tuple of parameter values
            
        Returns:
            List of result rows
        """
        cursor = self.db.cursor()
        cursor.execute(query, parameters)
        return cursor.fetchall()
    
    def _get_date_range(self, date_range=None):
        """
        Get a standardized date range tuple either from a provided string
        or using default all-time range.
        
        Args:
            date_range: Optional date range string
            
        Returns:
            Tuple of (start_date, end_date) or error message string
        """
        if date_range:
            return self.parse_date_range(date_range)
        else:
            return ("1900-01-01", "2100-12-31")  # Default full range
            
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
    
    def _format_monthly_category_report(self, results, year):
        """
        Format monthly category spending data into a matrix report.
        
        Args:
            results: Query results with monthly category spending
            year: Year for the report
            
        Returns:
            Formatted report string
        """
        # Extract unique months and categories from results
        months = sorted(set(row[0] for row in results))
        categories = sorted(set(row[1] for row in results))
        
        # Create a data structure for easy lookup
        spending_data = {}
        for row in results:
            month, category, amount = row
            if month not in spending_data:
                spending_data[month] = {}
            spending_data[month][category] = amount
        
        # Create the report
        report = f"Monthly Category Spending for {year}\n"
        report += "=" * len(report) + "\n\n"
        
        # Header row with category names
        header = "Month".ljust(12)
        for category in categories:
            header += category.ljust(15)
        header += "Total".ljust(15)
        report += header + "\n"
        
        # Separator line
        report += "-" * len(header) + "\n"
        
        # Month names - avoiding datetime dependency
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        # Data rows
        for month in months:
            month_name = month_names[int(month)-1]
            row_str = month_name.ljust(12)
            month_total = 0
            
            for category in categories:
                amount = spending_data.get(month, {}).get(category, 0)
                month_total += amount
                row_str += f"${amount:<14.2f}"
            
            row_str += f"${month_total:<14.2f}"
            report += row_str + "\n"
        
        return report
    
    def _get_highest_spenders_by_month(self, monthly_spending):
        """
        Determine the highest spender for each month from spending data.
        
        Args:
            monthly_spending: List of (month, username, amount) tuples
            
        Returns:
            Dictionary mapping month numbers to (username, amount) tuples
        """
        highest_spenders = {}
        
        for month, username, amount in monthly_spending:
            if month not in highest_spenders or amount > highest_spenders[month][1]:
                highest_spenders[month] = (username, amount)
                
        return highest_spenders
        
    def _format_highest_spenders_report(self, highest_spenders, year):
        """
        Format highest spender data into a report.
        
        Args:
            highest_spenders: Dictionary of month to (username, amount) tuples
            year: Year for the report
            
        Returns:
            Formatted report string
        """
        # Month names - avoiding datetime dependency
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        # Format the results
        report = f"Highest Spender Per Month for {year}\n"
        report += "=" * len(report) + "\n\n"
        
        # Column headers
        headers = ['Month', 'User', 'Amount Spent']
        
        # Prepare data rows
        data = []
        for month_num in sorted(highest_spenders.keys()):
            username, amount = highest_spenders[month_num]
            month_name = month_names[int(month_num)-1]
            data.append((month_name, username, amount))
        
        # Create tabular formatting
        col_widths = {
            'Month': max(len('Month'), max(len(row[0]) for row in data)) + 2,
            'User': max(len('User'), max(len(row[1]) for row in data)) + 2,
            'Amount Spent': len('Amount Spent') + 5
        }
        
        # Header row
        header_row = "Month".ljust(col_widths['Month']) + "User".ljust(col_widths['User']) + "Amount Spent".ljust(col_widths['Amount Spent'])
        report += header_row + "\n"
        report += "-" * sum(col_widths.values()) + "\n"
        
        # Data rows
        for month_name, username, amount in data:
            report += month_name.ljust(col_widths['Month']) + username.ljust(col_widths['User']) + f"${amount:.2f}".ljust(col_widths['Amount Spent']) + "\n"
        
        return report
    
    def _format_error(self, action, exception):
        """
        Format an error message consistently.
        
        Args:
            action: String describing the action that failed
            exception: The exception that occurred
            
        Returns:
            Formatted error message
        """
        return f"Error {action}: {str(exception)}"

    def _is_valid_date_format(self, date_str):
        """
        Validate a date string in YYYY-MM-DD format.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            Boolean indicating if the format is valid
        """
        try:
            year, month, day = date_str.split('-')
            return (len(year) == 4 and len(month) == 2 and len(day) == 2 and
                   1 <= int(month) <= 12 and 1 <= int(day) <= 31)
        except:
            return False

    def parse_date_range(self, date_range: str):
        """
        Parse a date range string into start and end date components.
        
        Args:
            date_range: String in format 'YYYY/MM/DD - YYYY/MM/DD' or 'YYYY - YYYY'
            
        Returns:
            Tuple of (start_date, end_date) or error message string
        """
        try:
            # Split the date range string
            if " to " in date_range:
                start_date, end_date = date_range.split(" to ")
            elif " - " in date_range:
                start_date, end_date = date_range.split(" - ")
            else:
                return "Invalid date range format. Use 'YYYY/MM/DD - YYYY/MM/DD' or 'YYYY - YYYY'"
            
            start_date = start_date.strip()
            end_date = end_date.strip()
            
            # Handle year-only format (YYYY - YYYY)
            if len(start_date) == 4 and start_date.isdigit() and len(end_date) == 4 and end_date.isdigit():
                start_date = f"{start_date}/01/01"  # Jan 1st of start year
                end_date = f"{end_date}/12/31"      # Dec 31st of end year
            
            # Convert date format from YYYY/MM/DD to YYYY-MM-DD for SQLite
            start_date = start_date.replace('/', '-')
            end_date = end_date.replace('/', '-')
            
            # Validate date format
            if not (self._is_valid_date_format(start_date) and self._is_valid_date_format(end_date)):
                return "Invalid date format. Use YYYY/MM/DD - YYYY/MM/DD or YYYY - YYYY"
                
            return (start_date, end_date)
            
        except Exception as e:
            return f"Error parsing date range: {str(e)}"

