from flask import Flask, request, render_template, url_for, redirect, flash, session
from forms import RegistrationForm, LoginForm  # Correct import for your forms
import pymysql

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Set a secret key for CSRF protection

# Set up the MySQL connection
def get_db_connection():
    connection = pymysql.connect(
        host='localhost',        # Replace with your MySQL server host
        user='root',             # Replace with your MySQL username
        password='',            # Replace with your MySQL password
        database='auth'         # Replace with your database name
    )
    return connection

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            # Query to find the user in the database
            cursor.execute('SELECT password FROM users WHERE username = %s', (username,))
            result = cursor.fetchone()

            if result is None:
                flash('Username does not exist. Please register first.', 'error')
                return redirect(url_for('register'))
            else:
                stored_password = result[0]
                if stored_password == password:  # Match password
                    # Log the user in by setting session
                    session['username'] = username
                    flash('Login successful!', 'success')
                    return redirect(url_for('book_appointment'))
                else:
                    flash('Incorrect password. Please try again.', 'error')
        except Exception as e:
            print(f"Error: {e}")
            flash('An error occurred during login. Please try again.', 'error')
        finally:
            cursor.close()
            connection.close()

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()  # Create the form instance
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # Open a database connection
        connection = get_db_connection()
        cursor = connection.cursor()

        # Execute SQL query to insert the data
        try:
            cursor.execute('INSERT INTO `users`(`username`, `email`, `password`) VALUES (%s, %s, %s)', (username, email, password))
            connection.commit()  # Commit the transaction
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            connection.rollback()  # Rollback in case of error
            print(f"Error: {e}")
            flash('An error occurred during registration. Please try again.', 'error')
        finally:
            cursor.close()
            connection.close()

    return render_template('register.html', form=form)

@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        date = request.form['date']
        time = request.form['time']
        reason = request.form['reason']

        # Open a database connection
        connection = get_db_connection()
        cursor = connection.cursor()

        # Execute SQL query to insert the booking data
        try:
            cursor.execute('INSERT INTO `appointments`(`name`, `date`, `time`, `reason`) VALUES (%s, %s, %s, %s)', 
                           (name, date, time, reason))
            connection.commit()  # Commit the transaction
            flash('Appointment booked successfully!', 'success')
        except Exception as e:
            connection.rollback()  # Rollback in case of error
            print(f"Error: {e}")
            flash('An error occurred while booking the appointment. Please try again.', 'error')
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('book_appointment'))  # Redirect to the appointment page after booking

    return render_template('book_appointment.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Fetch data
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM appointments')
        total_appointments = cursor.fetchone()[0]

        cursor.execute('SELECT name, date, time, reason FROM appointments ORDER BY date DESC LIMIT 5')
        recent_appointments = cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        total_users = total_appointments = 0
        recent_appointments = []
    finally:
        cursor.close()
        connection.close()

    return render_template('admin_dashboard.html', total_users=total_users, total_appointments=total_appointments, recent_appointments=recent_appointments)






@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Ensure the user is logged in by checking the session
    if 'username' not in session:
        flash('You need to log in first', 'warning')
        return redirect(url_for('login'))

    # Get user info from the database
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute('SELECT username, email FROM users WHERE username = %s', (session['username'],))
        user_info = cursor.fetchone()

        if not user_info:
            flash('User not found', 'error')
            return redirect(url_for('index'))
        else:
            username, email = user_info
    except Exception as e:
        flash('Error fetching user data.', 'error')
        print(e)
        return redirect(url_for('index'))
    finally:
        cursor.close()
        connection.close()

    return render_template('profile.html', username=username, email=email)




@app.route('/settings', methods=['GET', 'POST'])
def settings():
    # Ensure the user is logged in
    if 'username' not in session:
        flash('You need to log in first', 'warning')
        return redirect(url_for('login'))

    # Handle password change
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('settings'))

        # Validate old password and update to new one
        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute('SELECT password FROM users WHERE username = %s', (session['username'],))
            result = cursor.fetchone()

            if result and result[0] == old_password:  # Old password match
                cursor.execute('UPDATE users SET password = %s WHERE username = %s', (new_password, session['username']))
                connection.commit()
                flash('Password updated successfully!', 'success')
            else:
                flash('Incorrect old password', 'error')
        except Exception as e:
            print(f"Error: {e}")
            flash('An error occurred while updating the password.', 'error')
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('settings'))

    return render_template('settings.html')










@app.route('/logout')
def logout():
    # Remove user session data
    session.pop('username', None)  # Use the 'username' key from the session
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))  # Redirect to login page after logout

if __name__ == '__main__':
    app.run()
