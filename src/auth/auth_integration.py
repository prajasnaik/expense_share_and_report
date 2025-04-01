from src.auth.user_authentication import UserAuthentication

class ExpenseAuthIntegration:
    def __init__(
            self,
            db_path: str = "database/app.db"
        ) -> None:

        """
        Initialize the authentication integration for the expense sharing app
        
        Args:
            db_path: Path to the SQLite database
        """
        self.auth_manager = UserAuthentication(db_path=db_path)
        
        # Keep track of the currently logged-in user
        self.current_user = None
    
    def register_new_user(
            self, 
            username: str, 
            password: str, 
            is_admin: bool = False
        ) -> tuple[bool, str]:
        """
        Register a new user for the expense sharing app
        
        Returns:
            tuple: (success boolean, message string)
        """
        user_id = self.auth_manager.register_user(username, password, is_admin)
        
        if user_id:
            return True, f"User registered successfully with ID {user_id}"
        else:
            return False, "Registration failed. Username may already be in use."
    
    def login(
            self,
            username: str, 
            password: str
        ) -> tuple[bool, str]:
        """
        Log a user into the expense sharing app
        
        Returns:
            tuple: (success boolean, message string)
        """
        user_data = self.auth_manager.verify_user(username, password)
        
        if user_data:
            self.current_user = user_data
            return True, f"Welcome back, {username}!"
        else:
            return False, "Invalid username or password"
    
    def logout(
            self
        ) -> tuple[bool, str]:
        """Log out the current user"""
        if self.current_user:
            username = self.current_user.get('username')
            self.current_user = None
            return True, f"Goodbye, {username}!"
        else:
            return False, "No user is currently logged in"
    
    def change_password(
            self, 
            old_password: str, 
            new_password: str
        ) -> tuple[bool, str]:
        """
        Change the password for the currently logged-in user
        
        Returns:
            tuple: (success boolean, message string)
        """
        if not self.current_user:
            return False, "You must be logged in to change your password"
        
        # Verify the old password first
        username = self.current_user.get('username')
        if self.auth_manager.verify_user(username, old_password):
            user_id = self.current_user.get('user_id')
            if self.auth_manager.update_password(user_id, new_password):
                return True, "Password updated successfully"
            else:
                return False, "Failed to update password"
        else:
            return False, "Current password is incorrect"
    
    def get_current_user(
            self
        ) -> dict[str, str] | None:
        """
        Get the currently logged-in user
        
        Returns:
            dict: User data or None if no user is logged in
        """
        return self.current_user
    
    def is_admin(
            self
        ) -> bool:
        """
        Check if the currently logged-in user is an admin
        
        Returns:
            boolean: True if the user is an admin, False otherwise
        """
        if self.current_user:
            return self.current_user.get('is_admin', False)
        return False
    
    def set_user_admin_status(
            self,
            user_id: str, 
            is_admin: bool
        ) -> tuple[bool, str]:
        """
        Set or remove admin status for a user (requires current user to be admin)
        
        Returns:
            tuple: (success boolean, message string)
        """
        if not self.is_admin():
            return False, "You need admin privileges to perform this action"
        
        if self.auth_manager.set_admin_status(user_id, is_admin):
            status = "admin" if is_admin else "regular user"
            return True, f"User (ID: {user_id}) is now a {status}"
        else:
            return False, "Failed to update user status"
    
    def delete_user(
            self, 
            user_id: str
        ) -> tuple[bool, str]:
        """
        Soft delete a user (requires current user to be admin)
        
        Returns:
            tuple: (success boolean, message string)
        """
        if not self.is_admin():
            return False, "You need admin privileges to perform this action"
        
        # Prevent admin from deleting themselves
        if self.current_user and self.current_user.get('user_id') == user_id:
            return False, "You cannot delete your own account"
        
        if self.auth_manager.delete_user(user_id):
            return True, f"User (ID: {user_id}) has been deleted"
        else:
            return False, "Failed to delete user"