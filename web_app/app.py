from flask import Flask, render_template, redirect, url_for, request, session
import requests
import os

app = Flask(__name__) # flask app intialization
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

def login_required(f):
    """
    A decorator function that checks if a user is logged in
    before allowing access to a route.
    Args:
    f (function): The route handler function to be decorated.
    Returns:
    function: The decorated function that redirects to the login page
    if the user is not logged in.
    """
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/', strict_slashes=False)
@login_required
def home():
    """
    This function is a route handler for the root URL ('/').
    Returns:
    A rendered HTML template (home.html)
    """
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    This function handles the registration process for a new user.
    Returns:
    - If the request method is GET, it renders the 'register.html' template.
    - If the request method is POST and the registration is successful, it redirects
    to the '/login' URL.
    - If the request method is POST and the registration fails,
    it returns a 'Registration failed' message with a 400 status code.
    """
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


@app.route('/login', methods=['GET', 'POST'], strict_slashes=False)
def login():
    """
    This function handles the login process for the application.
    Returns:
    - If the request method is POST and the login is successful,
    it redirects to the '/' URL.
    - If the request method is POST and the login fails, it returns a
    'Login failed' message with a 401 status code.
    - If the request method is GET, it renders the 'login.html' template.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        response = requests.post('http://backend:6000/login', json={
            'username': username,
            'password': password
        })
        if response.status_code == 200:
            session['user_id'] = response.json()['user_id']
            return redirect('/')
        else:
            return 'Login failed', 401

    return render_template('login.html')

@app.route('/logout', methods=['GET'], strict_slashes=False)
def logout():
    """
    This function handles the logout process for the current user.
    Returns:
    - If the logout is successful, it redirects to the '/login' URL.
    - If the logout fails, it returns a 'Logout failed' message with a 401 status code.
    """
    response = requests.get('http://backend:6000/logout')
    if response.status_code == 200:
        return redirect('/login')

# Route for Register


@app.errorhandler(404)
def page_not_found(e):
    """
    Custom error handler for 404 Not Found error.
    Returns:
    A rendered HTML template (404.html) with a status code of 404.
    """
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='6000')
