import os
import json
from flask import Flask, render_template, request, Response, g
from ldap3 import Server, Connection, ALL, NTLM

app = Flask(__name__)

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def check_ad_credentials(username, password):
    """Verifies credentials and checks group membership via LDAP."""
    config = load_config()
    # Replace with your Domain Controller IP or Name
    ldap_server = "your_domain_controller.company.com" 
    domain = "YOURDOMAIN" # e.g., 'GLOBAL'
    
    try:
        server = Server(ldap_server, get_info=ALL)
        # Attempt to bind with the provided user credentials
        conn = Connection(server, user=f"{domain}\\{username}", password=password, authentication=NTLM)
        
        if not conn.bind():
            return False, None

        # Search for the user to get their groups
        # Search filter looks for the username in AD
        conn.search(
            search_base="DC=yourdomain,DC=com", 
            search_filter=f"(sAMAccountName={username})",
            attributes=['memberOf', 'mail', 'displayName']
        )
        
        if not conn.entries:
            return False, None
            
        user_entry = conn.entries[0]
        user_groups = user_entry.memberOf.value
        
        # Check if any of the user's AD groups match our config list
        authorized_groups = config['auth']['ad_groups']
        is_authorized = any(
            any(group in g_str for group in authorized_groups) 
            for g_str in user_groups
        )
        
        return is_authorized, user_entry.displayName.value

    except Exception as e:
        print(f"LDAP Error: {e}")
        return False, None

def requires_auth():
    """Sends a 401 response that enables basic auth popup."""
    return Response(
        'Could not verify your access level for that URL.\n'
        'Please login with your domain credentials.', 401,
        {'WWW-Authenticate': 'Basic realm="Login with Domain Account"'}
    )

@app.before_request
def ask_for_auth():
    config = load_config()
    if not config.get('auth', {}).get('enabled', True):
        return

    auth = request.authorization
    if not auth:
        return requires_auth()
    
    authorized, display_name = check_ad_credentials(auth.username, auth.password)
    if not authorized:
        return render_template('access_denied.html', user=auth.username), 403
    
    g.user_display_name = display_name

@app.route('/')
def index():
    return render_template('index.html', config=load_config(), user_id=g.user_display_name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
