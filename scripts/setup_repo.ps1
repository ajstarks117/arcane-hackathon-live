$repo_dir = "c:\Users\aryan\Arcane_Nexus\arcane-demo-repo"
mkdir $repo_dir -ErrorAction SilentlyContinue
cd $repo_dir
git init

New-Item -ItemType Directory -Force "tests"
New-Item -ItemType Directory -Force ".github\workflows"

Set-Content -Path "auth.py" -Value @"
def validate_user(username, password):
    if not username or not password:
        return False
    if username == `"admin`" and password == `"secret`":
        return True
    return False
"@

Set-Content -Path "api.py" -Value @"
from auth import validate_user

def login_endpoint(request_data):
    if `"username`" not in request_data or `"password`" not in request_data:
        return {`"status`": 400, `"message`": `"Missing credentials`"}
    if validate_user(request_data[`"username`"], request_data[`"password`"]):
        return {`"status`": 200, `"message`": `"Success`"}
    else:
        return {`"status`": 401, `"message`": `"Unauthorized`"}
"@

Set-Content -Path "middleware.py" -Value @"
from auth import validate_user

def auth_middleware(request):
    auth_header = request.get(`"headers`", {}).get(`"Authorization`", `"`)
    if not auth_header.startswith(`"Basic `"):
        return False
    
    try:
        credentials = auth_header.split(`" `")[1]
        username, password = credentials.split(`":`")
        return validate_user(username, password)
    except Exception:
        return False
"@

Set-Content -Path "tests\test_auth.py" -Value @"
from auth import validate_user

def test_validate_user_correct():
    assert validate_user(`"admin`", `"secret`") is True

def test_validate_user_incorrect_password():
    assert validate_user(`"admin`", `"wrong`") is False

def test_validate_user_incorrect_username():
    assert validate_user(`"wrong`", `"secret`") is False

def test_validate_user_empty():
    assert validate_user(`"`, `"`) is False

def test_validate_user_none():
    assert validate_user(None, None) is False
"@

Set-Content -Path "tests\test_api.py" -Value @"
from api import login_endpoint

def test_login_success():
    assert login_endpoint({`"username`": `"admin`", `"password`": `"secret`"}).get(`"status`") == 200

def test_login_unauthorized():
    assert login_endpoint({`"username`": `"admin`", `"password`": `"wrong`"}).get(`"status`") == 401

def test_login_missing_fields():
    assert login_endpoint({`"username`": `"admin`"}).get(`"status`") == 400
"@

Set-Content -Path "tests\test_middleware.py" -Value @"
from middleware import auth_middleware

def test_middleware_success():
    assert auth_middleware({`"headers`": {`"Authorization`": `"Basic admin:secret`"}}) is True

def test_middleware_failure():
    assert auth_middleware({`"headers`": {`"Authorization`": `"Basic admin:wrong`"}}) is False
"@

Set-Content -Path ".github\workflows\ci.yml" -Value @"
name: CI
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: `"3.10`"
    - name: Install pytest
      run: pip install pytest
    - name: Run tests
      run: pytest
"@

Set-Content -Path ".arcane_config.json" -Value @"
{ `"good_commit`": `"HEAD~3`" }
"@

git add .
git commit -m "Initial commit"

# Make 3 more commits on main to satisfy HEAD~3
Set-Content -Path "dummy1.txt" -Value "commit 1"
git add dummy1.txt
git commit -m "Commit 1"

Set-Content -Path "dummy2.txt" -Value "commit 2"
git add dummy2.txt
git commit -m "Commit 2"

Set-Content -Path "dummy3.txt" -Value "commit 3"
git add dummy3.txt
git commit -m "Commit 3"

# Bug 1 branch
git branch bug-1
git checkout bug-1

Set-Content -Path "auth.py" -Value @"
def validate_user(user, pwd):
    if not user or not pwd:
        return False
    if user == `"admin`" and pwd == `"secret`":
        return True
    return False
"@

git add auth.py
git commit -m "Introduce bug-1: Change validate_user signature"

# Bug 2 branch
git checkout main
git branch bug-2
git checkout bug-2

Set-Content -Path "auth.py" -Value @"
def validate_user(username, password):
    try:
        if not username.strip() or not password.strip():
            return False
    except AttributeError:
        # None doesn't have .strip()
        pass
    
    if not username or not password:
        return False
    # Let me introduce a distinct null-check bug
    # Wait, the bug is supposed to be a distinct null-check bug.
    # The requirement: "Create a second branch 'bug-2' with a similar but distinct null-check bug."
    # E.g. AttributeError: 'NoneType' object has no attribute 'strip'
    
    if username == `"admin`" and password == `"secret`":
        return True
    return False
"@
# Let's rewrite the bug-2 auth.py to just blindly call strip().
Set-Content -Path "auth.py" -Value @"
def validate_user(username, password):
    if len(username.strip()) == 0 or len(password.strip()) == 0:
        return False
    if username == `"admin`" and password == `"secret`":
        return True
    return False
"@

git add auth.py
git commit -m "Introduce bug-2: Null check bug"

git checkout main
