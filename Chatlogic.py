import smtplib
from email.message import EmailMessage
from smtplib import SMTPRecipientsRefused, SMTPException

def send_reset_email(recipient, token):
    msg = EmailMessage()
    msg['Subject'] = 'Password Reset Request'
    msg['From'] = 'your_email@example.com'
    msg['To'] = recipient
    reset_link = f"http://localhost:5000/reset/{token}"
    msg.set_content(f"Click the link to reset your password: {reset_link}")

    try:
        with smtplib.SMTP('smtp.example.com', 587) as smtp:
            smtp.starttls()
            smtp.login('your_email@example.com', 'your_password')
            smtp.send_message(msg)
        return True, None  # Success
    except SMTPRecipientsRefused as e:
        return False, "Email address not found in Exchange."
    except SMTPException as e:
        return False, f"SMTP error: {str(e)}"



@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            token = str(uuid.uuid4())
            success, error_msg = send_reset_email(email, token)
            if success:
                return 'Password reset link sent to your email.'
            else:
                return f'Error sending email: {error_msg}'
        else:
            return 'Email not found in our records.'

    return render_template('forgot.html')
