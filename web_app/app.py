from flask import Flask, render_template, redirect, url_for, request, session
import requests
import os

app = Flask(__name__) # flask app intialization
app.config['SECRET_KEY'] = os.urandom(24)

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # If the user is not logged in, redirect to the login page
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
@login_required
def home():
    """
    This function is a route handler for the root URL ('/').
    It renders the 'home.html' template when accessed.

    Parameters:
    None

    Returns:
    A rendered HTML template (home.html)
    """
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'], strict_slashes=False)
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        response = requests.post('http://backend:6000/login', json={
            'username': username,
            'password': password
        })
        if response.status_code == 200:
            session['user_id'] = response.json().get('user_id')
            return redirect('/')
        else:
            return 'Login failed', 401

    return render_template('login.html')

# Route for Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        response = requests.post('http://backend:6000/register', json={
            'username': username,
            'password': password
        })
        if response.status_code == 201:
            return redirect('/login')
        else:
            return 'Registration failed', 400

    return render_template('register.html')


@app.errorhandler(404)
def page_not_found(e):
    """
    Custom error handler for 404 Not Found error.
    This function is a route handler for the '/404' URL.
    It renders the '404.html' template when accessed.

    Parameters:
    e (Exception): The exception object that caused the error.

    Returns:
    A rendered HTML template (404.html) with a status code of 404.
    """
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='6000')
