# Initialising the the auth system
# auth = ExpenseAuthIntegration()

# # Register a new user
# success, message = auth.register_new_user("newuser", "password123")
# print(message)

# # Log in
# success, message = auth.login("newuser", "password123")
# print(message)

# # Check if user is logged in
# if auth.get_current_user():
#     print(f"Logged in as: {auth.get_current_user()['username']}")
#     print(f"Admin status: {auth.is_admin()}")

# # Log out
# success, message = auth.logout()
# print(message)