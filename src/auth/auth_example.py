from src.auth.user_authentication import UserAuthentication
import os
import sqlite3

# Ensure database directory exists
os.makedirs("database", exist_ok=True)

def ensure_db_exists():
    """Make sure the database file exists and has the required tables"""
    if not os.path.exists("database/app.db"):
        # Create a minimal database for testing if it doesn't exist
        conn = sqlite3.connect("database/app.db")
        cursor = conn.cursor()
        
        # Create the users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT 0,
            is_deleted BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

def main():
    # Make sure the database exists
    ensure_db_exists()
    
    # Initialize the authentication system
    auth_manager = UserAuthentication(db_path="database/app.db")
    
    # Example: Register a new user
    print("Registering new user...")
    user_id = auth_manager.register_user(
        username="johndoe", 
        password="securePassword123", 
        is_admin=False
    )
    
    if user_id:
        print(f"User registered successfully with ID: {user_id}")
    else:
        print("Username already exists")
    
    # Example: Register an admin user
    print("\nRegistering admin user...")
    admin_id = auth_manager.register_user(
        username="adminuser", 
        password="adminPass456", 
        is_admin=True
    )
    
    if admin_id:
        print(f"Admin user registered successfully with ID: {admin_id}")
    else:
        print("Username already exists")
    
    # Example: Verify user credentials
    print("\nVerifying regular user credentials...")
    user_data = auth_manager.verify_user("johndoe", "securePassword123")
    
    if user_data:
        print("User authenticated successfully!")
        print(f"User data: {user_data}")
        print(f"Is admin: {user_data['is_admin']}")
    else:
        print("Invalid username or password")
    
    # Example: Verify admin credentials
    print("\nVerifying admin user credentials...")
    admin_data = auth_manager.verify_user("adminuser", "adminPass456")
    
    if admin_data:
        print("Admin authenticated successfully!")
        print(f"Admin data: {admin_data}")
        print(f"Is admin: {admin_data['is_admin']}")
    else:
        print("Invalid username or password")
    
    # Example: Update user password
    print("\nUpdating user password...")
    if user_id and auth_manager.update_password(user_id, "newSecurePassword456"):
        print("Password updated successfully")
        
        # Verify with the new password
        print("\nVerifying with new password...")
        user_data = auth_manager.verify_user("johndoe", "newSecurePassword456")
        
        if user_data:
            print("User authenticated successfully with new password!")
        else:
            print("Authentication failed with new password")
    else:
        print("Failed to update password")
    
    # Example: Set admin status for a regular user
    print("\nChanging user to admin...")
    if auth_manager.set_admin_status(user_id, True):
        print("User is now an admin")
        user_data = auth_manager.get_user_by_id(user_id)
        print(f"Updated user data: {user_data}")
    else:
        print("Failed to change admin status")
    
    # Example: Delete a user (soft delete)
    print("\nDeleting admin user...")
    if auth_manager.delete_user(admin_id):
        print("Admin user deleted successfully")
        
        # Try to authenticate with deleted user
        admin_data = auth_manager.verify_user("adminuser", "adminPass456")
        if admin_data:
            print("Warning: Deleted user can still authenticate!")
        else:
            print("Deleted user cannot authenticate (expected behavior)")
    else:
        print("Failed to delete admin user")

if __name__ == "__main__":
    main()