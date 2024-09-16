from flask import Flask, make_response, jsonify, request, abort, session
from flask_pymongo import PyMongo
import logging
from flask_cors import CORS
from datetime import datetime, timedelta
import google.generativeai as genai
from markdown import markdown
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os


genai.configure(api_key='AIzaSyDCKpjPKsWbDdlBtnQItbSwxkeHlSUqefE')  # api key for AI model
model = genai.GenerativeModel('gemini-1.5-flash') # assign default model
chat = model.start_chat(history=[]) # create chat history
app = Flask(__name__) # Flask
app.config['SECRET_KEY'] = "hamada" # setting the secret key

app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True # works in http only while our development
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1) # session ends automatically after one hour

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

# MongoDB config
app.config['MONGO_URI'] = 'mongodb://root:root_password@mongodb:27017/flask_db?authSource=admin'
logging.basicConfig()  # logging configuration
mongo = PyMongo(app) # initialize mongo instance from pymongo


@app.errorhandler(404)
def not_found(error):
    """
    Error handler for 404 Not Found error.

    Returns:
    flask.Response: A JSON response with a 'error' key containing
    the custom error message and HTTP status code 404.
    """
    return make_response(jsonify({'error': "Not found"}), 404)


@app.route('/register', methods=['POST'])
def register():
    """
    Registers a new user in the database.

    Returns:
    flask.Response: A JSON response with a success message or
    an error message and HTTP status code.
    - If the username already exists, returns a JSON response with
    'User already exists' message and HTTP status code 400.
    - If the user is successfully registered, returns a JSON response with
    'User registered successfully' message and HTTP status code 201.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if mongo.db.users.find_one({'username': username}):
        return jsonify({'message': 'User already exists'}), 400

    hashed_password = generate_password_hash(password)
    new_user = {
        'username': username,
        'password': hashed_password
    }
    mongo.db.users.insert_one(new_user)

    return jsonify({'message': 'User registered successfully'}), 201


# Login route
@app.route('/login', methods=['POST'])
def login():
    """
    Authenticates a user by verifying their username and password.

    Returns:
    - flask.Response: A JSON response with a success message and user ID if the
    credentials are valid.
    Returns a JSON response with an error message if the credentials are invalid.
    HTTP status code 200 for successful login, 401 for invalid credentials.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = mongo.db.users.find_one({'username': username})

    if user and check_password_hash(user['password'], password):
        return jsonify({'message': 'Login successful', 'user_id': str(user['_id'])}), 200
    return jsonify({'message': 'Invalid credentials'}), 401


@app.route('/logout')
def logout():
    """
    Logs out the current user by removing the 'user_id' from the session.

    Returns:
    flask.Response: A JSON response with a success message and HTTP status code 200.
    The response contains the following keys:
    - 'message': A string indicating the success of the logout operation.
    """
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200


@app.route('/notes', methods=['GET'], strict_slashes=False)
def get_all_notes():
    """
    Retrieves all notes for the currently logged-in user.
    
    Returns:
    flask.Response: A JSON response containing a list of all notes for the user.
    Each note is represented as a dictionary with the following keys:
    If the user is not logged in, returns a JSON response with an error message
    and HTTP status code 401.
    """
    user_id = ObjectId(session['user_id'])

    if not user_id:
        return jsonify({'error': 'User not logged in!'}), 401

    all_notes = mongo.db.notes.find({'user_id': user_id})
    lis = []
    mynotes = "notes: "
    i = 1
    for note in all_notes:
        list_notes = {
            'notes_id': str(note['_id']),
            'title': note['title'],
            'content': note['content'],
            'created_at': note['created_at'],
            'updated_at': note['updated_at']
        }
        mynotes += str(i) + "- " + note['title'] + ': "' + note['content'] + '"'
        lis.append(list_notes)
        i = i + 1
    chat.send_message("i will send some notes to use it in future questions\n" + mynotes)
    return jsonify(lis), 200


@app.route('/notes', methods=['POST'], strict_slashes=False)
def add_note():
    """
    Add a new note to the database.

    Returns:
    flask.Response: A JSON response with a success message
    and HTTP status code 201 if the note is added successfully.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in!'}), 401

    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    new_note = {
        'user_id': ObjectId(session['user_id']),
        'title': title,
        'content': content,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    mongo.db.notes.insert_one(new_note)
    return jsonify({'message': 'Note added successfully!'}), 201


@app.route('/notes/<string:id>', methods=['DELETE'], strict_slashes=False)
def delete_note(id):
    """
    Deletes a note from the database based on the provided note ID.

    Returns:
    flask.Response: A JSON response with a success message and HTTP status code 200
    if the note is deleted successfully. If the note with the given ID does not exist,
    returns a 404 Not Found error.
    """
    note = mongo.db.notes.find_one({'_id': ObjectId(id)})
    if note:
        mongo.db.notes.delete_one({'_id': ObjectId(id)})
        return jsonify({'message': 'Note deleted successfully!'}), 200
    else:
        return abort(404)


@app.route('/notes/ai', methods=['POST'], strict_slashes=False)
def ai_chat():
    """
    This function handles the AI chat functionality. 
    It receives a prompt from the client,
    sends it to the AI model for processing, and returns
    the AI's response in markdown format.

    Returns:
    - flask.Response: A JSON response containing
    the AI's response in markdown format.
      The response has the following structure:
      {
          'AI': str  (The AI's response in markdown format)
      }
      HTTP status code 201 is returned if the operation is successful.
    """
    data = request.get_json()
    prompt = data.get('prompt')
    response = chat.send_message(prompt)
    return jsonify({'AI': markdown(response.text)}), 201


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6000, threaded=True)
