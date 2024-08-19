from flask import Flask, render_template, request, redirect,session, url_for, flash
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Kisanjena@123'
app.config['MYSQL_DB'] = 'user_database'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

@app.route('/')
def landing_page():
    return render_template('landing_page.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check for existing email
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            flash('Email already exists. Please use a different email address.', 'danger')
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert user details into the database
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
        mysql.connection.commit()
        cur.close()

        flash('You have successfully signed up!', 'success')
        return redirect(url_for('login'))
    
    # Render the template with the show_signup flag set to True
    return render_template('login.html', show_signup=True)




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Retrieve user details from the database
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()

        if user is None:
            # Username doesn't exist
            flash('Username not found.', 'danger')
            return redirect(url_for('login'))

        # Check if the password matches
        if not bcrypt.check_password_hash(user[3], password):
            flash('Incorrect password.', 'danger')
            return redirect(url_for('login'))

        # Successful login
        session['user_id'] = user[0]
        flash('Login successful!', 'success')
        return redirect(url_for('landing_page'))

    return render_template('login.html', show_signup=False)


@app.route('/dashboard')
def dashboard():
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))
    return render_template('page1.html')

@app.route('/logout')
def logout():
    # Clear the session to log the user out
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('landing_page'))

@app.route('/get_started')
def get_started():
    # Check if the user is logged in by verifying the session
    if 'user_id' in session:
        # If logged in, redirect to the dashboard (page1)
        return redirect(url_for('dashboard'))
    else:
        # If not logged in, redirect to the login page
        return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
