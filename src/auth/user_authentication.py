import sqlite3
from auth import UserAuth

class UserAuthentication:
    def __init__(self, db_path="database/app.db"):
        """
        Initialize the user authentication manager
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self.auth = UserAuth()
    
    def _get_connection(self):
        """Create and return a database connection"""
        return sqlite3.connect(self.db_path)
    
    def register_user(self, username, password, is_admin=False):
        """
        Register a new user with an encrypted password
        
        Args:
            username: Username for the new user
            password: Plain text password to be encrypted
            is_admin: Boolean indicating if user is admin
            
        Returns:
            user_id if successful, None if username already exists
        """
        # Encrypt the password using the UserAuth class
        password_hash = self.auth.encode(password)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO users (username, password_hash, is_admin)
            VALUES (?, ?, ?)
            ''', (username, password_hash, is_admin))
            
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
            
        except sqlite3.IntegrityError:
            # Username already exists
            return None
        finally:
            conn.close()
    
    def verify_user(self, username, password):
        """
        Verify user credentials
        
        Args:
            username: Username to verify
            password: Plain text password to check
            
        Returns:
            User data dictionary if credentials are valid, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT user_id, username, password_hash, is_admin
        FROM users
        WHERE username = ? AND is_deleted = 0
        ''', (username,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data:
            return None
        
        # Get the encrypted password from the database
        password_hash = user_data[2]
        
        # Decrypt the password
        try:
            decrypted_password = self.auth.decode(password_hash)
            
            # Check if the provided password matches the decrypted one
            if password == decrypted_password:
                return {
                    'user_id': user_data[0],
                    'username': user_data[1],
                    'is_admin': bool(user_data[3])
                }
        except Exception:
            # Decryption failed or password doesn't match
            pass
        
        return None
    
    def update_password(self, user_id, new_password):
        """
        Update a user's password
        
        Args:
            user_id: ID of the user whose password is being updated
            new_password: New password to encrypt and store
            
        Returns:
            True if successful, False otherwise
        """
        # Encrypt the new password
        password_hash = self.auth.encode(new_password)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE users
            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND is_deleted = 0
            ''', (password_hash, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True
            else:
                return False
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id):
        """
        Get user information by ID
        
        Args:
            user_id: ID of the user to retrieve
            
        Returns:
            User data dictionary if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT user_id, username, is_admin
        FROM users
        WHERE user_id = ? AND is_deleted = 0
        ''', (user_id,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return {
                'user_id': user_data[0],
                'username': user_data[1],
                'is_admin': bool(user_data[2])
            }
        
        return None
        
    def delete_user(self, user_id):
        """
        Soft delete a user (set is_deleted flag to 1)
        
        Args:
            user_id: ID of the user to delete
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE users
            SET is_deleted = 1, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            ''', (user_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True
            else:
                return False
        finally:
            conn.close()
            
    def set_admin_status(self, user_id, is_admin):
        """
        Set or unset admin status for a user
        
        Args:
            user_id: ID of the user to update
            is_admin: Boolean indicating if user should be admin
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE users
            SET is_admin = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND is_deleted = 0
            ''', (is_admin, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True
            else:
                return False
        finally:
            conn.close()