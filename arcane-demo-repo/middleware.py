from auth import validate_user

def auth_middleware(request):
    headers = request.get("headers", {})
    return validate_user(headers.get("user"), headers.get("pass"))

