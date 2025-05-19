import getpass  # Already in standard library

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Get current OS user
        os_user = getpass.getuser()

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, email FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if result and check_password_hash(result[0], password):
            user_email = result[1]

            # Compare OS user with expected login (e.g., matching email username part)
            if os_user.lower() in user_email.lower():
                session['username'] = username
                return redirect(url_for('index'))
            else:
                return 'OS login does not match user email'
        else:
            return 'Invalid credentials'
    return render_template('login.html')
