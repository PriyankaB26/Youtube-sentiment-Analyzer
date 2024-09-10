import io
from flask import Flask, jsonify, render_template, request, redirect, send_file, session, url_for, flash
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'login_reg_db'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

# In-memory storage for OTP (for simplicity)
otp_storage = {}

# def send_otp(email, otp):
#     sender_email = "your_email@gmail.com"  # Replace with your Gmail address
#     receiver_email = email
#     password = "your_app_password"  # Replace with your Gmail app-specific password

#     message = MIMEMultipart()
#     message["From"] = sender_email
#     message["To"] = receiver_email
#     message["Subject"] = "Your OTP for Password Reset"

#     body = f"Your OTP for password reset is {otp}"
#     message.attach(MIMEText(body, "plain"))

#     server = smtplib.SMTP("smtp.gmail.com", 587)
#     server.starttls()
#     server.login(sender_email, password)
#     text = message.as_string()
#     server.sendmail(sender_email, receiver_email, text)
#     server.quit()

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
    
    return render_template('login.html', show_signup=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Retrieve user details from the database
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", [email])
        user = cur.fetchone()
        cur.close()

        if user is None:
            flash('Email not found.', 'danger')
            return redirect(url_for('login'))

        # Check if the password matches
        if not bcrypt.check_password_hash(user[3], password):
            flash('Incorrect password.', 'danger')
            return redirect(url_for('login'))

        # Successful login
        session['user_id'] = user[0]
        session['user_email'] = user[2]  # Store user email in session
        flash('Login successful!', 'success')
        return redirect(url_for('landing_page'))

    return render_template('login.html', show_signup=False)

@app.route('/logout')
def logout():
    session.clear()  # Clear the session completely
    flash('You have been logged out.', 'info')
    return redirect(url_for('landing_page'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST' and request.form.get('action') == 'get-started-3':
        return redirect(url_for('page2'))

    return render_template('page1.html')

@app.route('/get_started')
def get_started():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

# @app.route('/forgot_password', methods=['GET', 'POST'])
# def forgot_password():
#     if request.method == 'POST':
#         email = request.form['email']

#         # Check if the email exists in the database
#         cur = mysql.connection.cursor()
#         cur.execute("SELECT * FROM users WHERE email = %s", [email])
#         user = cur.fetchone()

#         if user:
#             # Generate and store OTP
#             otp = random.randint(1000, 9999)  # 4-digit OTP
#             otp_storage[email] = otp

#             # Send OTP to user's email
#             send_otp(email, otp)
#             flash('OTP sent to your email.', 'info')
#             return render_template('forgot_password.html', otp_sent=True, email=email)
#         else:
#             flash('Email not found.', 'danger')

#     return render_template('forgot_password.html', otp_sent=False)

# @app.route('/reset_password', methods=['POST'])
# def reset_password():
#     email = request.form['email']
#     entered_otp = request.form['otp']
#     new_password = request.form['new_password']

#     # Verify OTP
#     if otp_storage.get(email) == int(entered_otp):
#         # Hash the new password
#         hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

#         # Update the password in the database
#         cur = mysql.connection.cursor()
#         cur.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
#         mysql.connection.commit()
#         cur.close()

#         # Clear the OTP
#         otp_storage.pop(email, None)

#         flash('Password has been reset successfully.', 'success')
#         return redirect(url_for('login'))
#     else:
#         flash('Invalid OTP. Please try again.', 'danger')
#         return render_template('forgot_password.html', otp_sent=True, email=email)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Acess denied, user should Login', 'warning')
        return redirect(url_for('landing_page'))

    user_id = session['user_id']

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')

        # Update name and email in the database
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET username = %s, email = %s WHERE id = %s", (name, email, user_id))

        # Check if a new profile image is uploaded
        if 'profile_image' in request.files:
            image = request.files['profile_image']
            if image and allowed_file(image.filename):
                image_data = image.read()
                cur.execute("UPDATE users SET profile_image = %s WHERE id = %s", (image_data, user_id))

        mysql.connection.commit()
        cur.close()

        # flash('Profile updated successfully!', 'success')
        return jsonify({'success': True})

    # Retrieve user details including the profile image
    cur = mysql.connection.cursor()
    cur.execute("SELECT username, email, profile_image FROM users WHERE id = %s", [user_id])
    user_data = cur.fetchone()
    cur.close()

    username, email, profile_image = user_data

    # Serve the image if it exists
    image_url = None
    if profile_image:
        image_url = url_for('get_profile_image')
    else:
        image_url = url_for('static', filename='default-avatar.png')

    return render_template('profile.html', username=username, email=email, image_url=image_url)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/get_profile_image')
def get_profile_image():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT profile_image FROM users WHERE id = %s", [user_id])
    profile_image = cur.fetchone()[0]
    cur.close()

    if profile_image:
        return send_file(io.BytesIO(profile_image), mimetype='image/png')  # Adjust mimetype if necessary
    else:
        return redirect(url_for('static', filename='default-avatar.png'))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/search', methods=['POST'])
def search():
    channel_url = request.form.get('channel_url')
    # Process the URL and perform the necessary operations
    # For example, you might want to analyze the channel URL
    # and return some results or render a template with results.

    # For now, let's just render a placeholder template.
    return render_template('search_results.html', channel_url=channel_url)

@app.route('/page2')
def page2():
    return render_template('page2.html')

if __name__ == "__main__":
    app.run(debug=True, port=5001)
