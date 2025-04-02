import sqlite3
from src.auth.auth import UserAuth

# Initialize the UserAuth class for password encryption
auth = UserAuth()

def hash_password(password):
    """
    Hash a password using RSA encryption
    
    Args:
        password: The plaintext password to hash
        
    Returns:
        The hashed password as a string
    """
    return auth.encode(password)

def verify_password(hashed_password, plaintext_password):
    """
    Verify a password against its hash
    
    Args:
        hashed_password: The hashed password from the database
        plaintext_password: The plaintext password to check
        
    Returns:
        True if the password matches, False otherwise
    """
    try:
        decrypted = auth.decode(hashed_password)
        return decrypted == plaintext_password
    except Exception:
        return False

def create_user(username, password, is_admin=False):
    """
    Create a new user with a hashed password
    
    Args:
        username: The username for the new user
        password: The plaintext password
        is_admin: Whether the user should be an admin
        
    Returns:
        user_id if successful, None otherwise
    """
    # Hash the password
    password_hash = hash_password(password)
    
    # Connect to the database
    conn = sqlite3.connect('database/app.db')
    cursor = conn.cursor()
    
    try:
        # Insert the new user with the hashed password
        cursor.execute('''
        INSERT INTO users (username, password_hash, is_admin)
        VALUES (?, ?, ?)
        ''', (username, password_hash, is_admin))
        
        # Get the new user ID
        user_id = cursor.lastrowid
        
        # Commit the changes
        conn.commit()
        
        return user_id
    except sqlite3.IntegrityError:
        # Username already exists
        return None
    finally:
        conn.close()

def authenticate_user(username, password):
    """
    Authenticate a user
    
    Args:
        username: The username to check
        password: The plaintext password to verify
        
    Returns:
        User data dictionary if authenticated, None otherwise
    """
    # Connect to the database
    conn = sqlite3.connect('database/app.db')
    cursor = conn.cursor()
    
    # Find the user
    cursor.execute('''
    SELECT user_id, username, password_hash, is_admin
    FROM users
    WHERE username = ? AND is_deleted = 0
    ''', (username,))
    
    user_data = cursor.fetchone()
    conn.close()
    
    if not user_data:
        return None
    
    # Check the password
    if verify_password(user_data[2], password):
        return {
            'user_id': user_data[0],
            'username': user_data[1],
            'is_admin': bool(user_data[3])
        }
    
    return None

def main():
    """Example of using the password hashing functions"""
    # Example password
    password = "MySecurePassword123"
    
    # Hash the password
    hashed_password = hash_password(password)
    print(f"Original password: {password}")
    print(f"Hashed password: {hashed_password}")
    
    # Verify the password
    is_valid = verify_password(hashed_password, password)
    print(f"Password verification: {'Successful' if is_valid else 'Failed'}")
    
    # Create a new user
    user_id = create_user("testuser", password)
    if user_id:
        print(f"Created user with ID: {user_id}")
        
        # Authenticate the user
        user_data = authenticate_user("testuser", password)
        if user_data:
            print(f"Authentication successful: {user_data}")
        else:
            print("Authentication failed")
    else:
        print("Failed to create user (username may already exist)")

if __name__ == "__main__":
    main()