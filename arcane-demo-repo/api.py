from auth import validate_user

def handle_login(data):
    return validate_user(data.get("username"), data.get("password"))

