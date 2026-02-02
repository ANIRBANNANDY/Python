import os
import json
import win32api
import win32security
from flask import Flask, render_template, g, abort, jsonify

app = Flask(__name__)

# --- CONFIGURATION LOADER ---
def load_config():
    """Load configuration from the central JSON file."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

# --- AD AUTHENTICATION LOGIC ---
def verify_ad_access():
    """
    Check if the current Windows user belongs to the 
    authorized AD groups defined in config.json.
    """
    config = load_config()
    
    # If auth is disabled in config, bypass check
    if not config.get('auth', {}).get('enabled', True):
        return True, "Guest_Mode"

    try:
        # Get the username of the person accessing the app
        current_user = win32api.GetUserName()
        authorized_groups = config['auth'].get('ad_groups', [])

        # Open the access token for the current process
        token = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(), 
            win32security.TOKEN_QUERY
        )
        
        # Retrieve all Group SIDs associated with this token
        groups = win32security.GetTokenInformation(token, win32security.TokenGroups)

        for (sid, attributes) in groups:
            try:
                # Convert SID to readable Name and Domain
                name, domain, type = win32security.LookupAccountSid(None, sid)
                if name in authorized_groups:
                    return True, current_user
            except:
                continue # Skip SIDs that cannot be resolved
        
        return False, current_user
    except Exception as e:
        print(f"Authentication Error: {e}")
        return False, "Unknown_User"

# --- MIDDLEWARE: SECURITY GATEKEEPER ---
@app.before_request
def restrict_access():
    """Runs before every request to ensure AD compliance."""
    # Skip ACL check for static assets (CSS/JS) to avoid flickering
    if '/static/' in g.get('path', ''):
        return

    allowed, user = verify_ad_access()
    if not allowed:
        # Return the Access Denied template with 403 Forbidden status
        return render_template('access_denied.html', user=user), 403
    
    # Store the authorized username for use in templates
    g.user_id = user

# --- ROUTES ---
@app.route('/')
def index():
    """Main Dashboard Route."""
    config = load_config()
    return render_template(
        'index.html', 
        config=config, 
        user_id=g.user_id
    )

@app.route('/get-config')
def get_config_js():
    """Returns config to the frontend JS (for IP lists/ports)."""
    return jsonify(load_config())

# --- ERROR HANDLERS ---
@app.errorhandler(403)
def forbidden(e):
    return render_template('access_denied.html', user="Unauthorized"), 403

if __name__ == '__main__':
    # Listen on all interfaces so it's accessible via Server 1's IP
    # Defaulting to port 8080 as per your previous setup
    config = load_config()
    port = config.get('hub_port', 8080)
    
    print(f"*** Hub Dashboard Started ***")
    print(f"Authorized Groups: {config['auth']['ad_groups']}")
    print(f"Running on: http://0.0.0.0:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
