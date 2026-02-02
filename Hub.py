import win32api
import win32security
import json
from flask import Flask, render_template, g, abort

app = Flask(__name__)

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def is_authorized():
    config = load_config()
    if not config.get('auth', {}).get('enabled', False):
        return True, "AuthDisabled"

    try:
        current_user = win32api.GetUserName()
        authorized_groups = config['auth']['ad_groups']
        
        # Get the token for the current process
        token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32security.TOKEN_QUERY)
        # Get all SIDs associated with the current user
        groups = win32security.GetTokenInformation(token, win32security.TokenGroups)
        
        for (sid, attr) in groups:
            # Convert SID to a readable group name
            try:
                name, domain, type = win32security.LookupAccountSid(None, sid)
                if name in authorized_groups:
                    return True, current_user
            except:
                continue # Skip SIDs that don't resolve
                
        return False, current_user
    except Exception as e:
        print(f"ACL Error: {e}")
        return False, "Error"

@app.before_request
def security_check():
    allowed, user = is_authorized()
    if not allowed:
        return render_template('access_denied.html', user=user), 403
    g.user_id = user

@app.route('/')
def index():
    return render_template('index.html', config=load_config(), user_id=g.user_id)
