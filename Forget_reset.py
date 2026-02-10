import random
import string
import smtplib
from email.mime.text import MIMEText

# Global dictionary to store temporary reset tokens (clears on app restart)
reset_tokens = {}

@app.route('/forgot-pin', methods=['GET', 'POST'])
def forgot_pin():
    if request.method == 'POST':
        # Rate Limiter: Max 3 attempts per session
        attempts = session.get('reset_attempts', 0)
        if attempts >= 3:
            flash("Rate limit reached. Please contact your system administrator.")
            return render_template('login.html')

        user = request.form.get('username').strip().lower()
        db = get_db_connection()
        record = db.execute('SELECT email FROM users WHERE username = ?', (user,)).fetchone()
        db.close()

        if record and record['email']:
            session['reset_attempts'] = attempts + 1
            
            # Generate 6-digit random token
            token = ''.join(random.choices(string.digits, k=6))
            reset_tokens[user] = token
            
            # --- SMTP EMAIL SENDING ---
            try:
                config = load_config()['smtp_settings']
                msg = MIMEText(f"Hello,\n\nYour 6-digit security token to reset your Process Monitor PIN is: {token}\n\nThis token will expire if the server restarts.")
                msg['Subject'] = 'PIN Reset Token - Process Monitor'
                msg['From'] = config['sender']
                msg['To'] = record['email']

                with smtplib.SMTP(config['server'], config['port']) as server:
                    # server.starttls() # Uncomment if your relay uses TLS
                    # server.login("svc_user", "password") # Uncomment if relay requires auth
                    server.send_message(msg)
                
                flash(f"A 6-digit token has been sent to {record['email']}")
                return render_template('reset_confirm.html', username=user)
            except Exception as e:
                print(f"SMTP Error: {e}")
                flash("Error sending email. Please check server logs.")
        else:
            flash("User ID not found or account never initialized.")
            
    return render_template('forgot_pin.html')

@app.route('/reset-confirm', methods=['POST'])
def reset_confirm():
    user = request.form.get('username')
    token = request.form.get('token').strip()
    new_pin = request.form.get('new_pin').strip()

    # Verify Token
    if reset_tokens.get(user) == token:
        # Check PIN Complexity
        is_ok, err = is_valid_pin_strict(new_pin)
        if not is_ok:
            flash(err)
            return render_template('reset_confirm.html', username=user)

        # Update Database
        db = get_db_connection()
        hashed_pin = hashlib.sha256(new_pin.encode()).hexdigest()
        db.execute('UPDATE users SET pin_hash = ? WHERE username = ?', (hashed_pin, user))
        db.commit()
        db.close()
        
        # Cleanup
        reset_tokens.pop(user, None)
        flash("PIN updated successfully! You can now login.")
        return redirect(url_for('login'))
    else:
        flash("Invalid or expired token.")
        return render_template('reset_confirm.html', username=user)
