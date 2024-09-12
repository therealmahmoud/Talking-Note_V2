from flask import Flask, make_response, jsonify, request, abort, render_template, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
import logging
from flask_cors import CORS
import google.generativeai as genai
from markdown import markdown
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash


genai.configure(api_key='AIzaSyDCKpjPKsWbDdlBtnQItbSwxkeHlSUqefE')  # api key for AI model
model = genai.GenerativeModel('gemini-1.5-flash') # assign default model
chat = model.start_chat(history=[]) # create chat history
app = Flask(__name__) # Flask
CORS(app)  # Enable CORS for all routes


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://flask_user:flask_password@mysql/flask_db'
logging.basicConfig() # logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO) # logging

db = SQLAlchemy(app)


@app.errorhandler(404)
def not_found(error):
    """
    Custom error handler for 404 Not Found error.
    Parameters:
    error (Exception): The original exception
    that triggered this error handler.

    Returns:
    flask.Response: A JSON response with a 'error' key
    containing the message "Not found",and an HTTP status code of 404.
    """
    return make_response(jsonify({'error': "Not found"}), 404)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=25)],
                           render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=25)],
                           render_kw={"placeholder": "Username"})
    submit = SubmitField("Register")
    
    def validate_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user:
            raise ValidationError('Username already exists!')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=25)],
                           render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=25)],
                           render_kw={"placeholder": "Username"})
    submit = SubmitField("Login")


class Notes(db.Model):
    """
    A class representing a note in the database.

    Attributes:
    notes_id (int): The unique identifier for the note.
    title (str): The title of the note.
    content (str): The content of the note.
    created_at (datetime): The timestamp when the note was created.
    updated_at (datetime): The timestamp when the note was last updated.
    """
    __tablename__ = 'notes'
    notes_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(45), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

with app.app_context():
    db.create_all() # creates the query objects before starting API's


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 400

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200


@app.route('/notes', methods=['GET'], strict_slashes=False)
def get_all_notes():
    """
    Retrieve all notes from the database.
    Returns:
    flask.Response: A JSON response containing a list of all notes,
    each represented as a dictionary with keys 'notes_id', 'title', 'content',
    'created_at', and 'updated_at'.
    HTTP status code 200 if the notes are retrieved successfully.
    """
    all_notes = Notes.query.all()
    lis = []
    mynotes = "notes: "
    i = 1
    for note in all_notes:
        list_notes = {
                'notes_id': note.notes_id,
                'title': note.title,
                'content': note.content,
                'created_at': note.created_at,
                'updated_at': note.updated_at
            }
        mynotes += str(i) + "- " + note.title + ': ' + note.content
        lis.append(list_notes)
        i = i + 1
    chat.send_message("i will send some notes to use it in future questions\n" + mynotes)
    return jsonify(lis), 200


@app.route('/notes/<int:id>', methods=['GET'], strict_slashes=False)
def get_notes_id(id):
    """
    Retrieve a note by its ID.

    Parameters:
    id (int): The ID of the note to be retrieved.

    Returns:
    flask.Response: A JSON response containing the note's details
    with HTTP status code 200 if the note is found.
    flask.abort: An HTTP 404 error if the note with the given ID doesn't exist.
    """
    note = Notes.query.filter_by(notes_id=id).first()
    if note:
        return jsonify({
            'notes_id': note.notes_id,
            'title': note.title,
            'content': note.content,
            'created_at': note.created_at,
            'updated_at': note.updated_at
        }), 200
    else:
        return abort(404)


@app.route('/notes', methods=['POST'], strict_slashes=False)
def add_note():
    """
    Add a new note to the database.
    Returns:
    flask.Response: A JSON response with a success message
    and HTTP status code 201
    if the note is added successfully.
    """
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    new_note = Notes(title=title, content=content)
    db.session.add(new_note)
    db.session.commit()
    return jsonify({'message': 'Note added successfully!'}), 201


@app.route('/notes/<int:id>', methods=['DELETE'], strict_slashes=False)
def delete_note(id):
    """
    Delete a note by its ID.
    Parameters:
    id (int): The ID of the note to be deleted.

    Returns:
    jsonify: A JSON response with a success message and HTTP status code 200
    if the note is deleted successfully.
    abort: An HTTP 404 error if the note with the given ID does not exist.
    """
    note = Notes.query.filter_by(notes_id=id).first()
    if note:
        db.session.delete(note)
        db.session.commit()
        return jsonify({'message': 'Note deleted successfully!'}), 200
    else:
        return abort(404)


@app.route('/notes/<int:id>', methods=['PUT'], strict_slashes=False)
def update_note(id):
    """
    Update a note by its ID.
    Parameters:
    id (int): The ID of the note to be updated.

    Returns:
    jsonify: A JSON response with a success message and HTTP status code 200
    if the note is updated successfully.
    abort: An HTTP 404 error if the note with the given ID does not exist.
    """
    note = Notes.query.filter_by(notes_id=id).first()
    if note:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        note.title = title
        note.content = content
        db.session.commit()
        return jsonify({'message': 'Note updated successfully!'}), 200
    return abort(404)


@app.route('/notes/ai', methods=['POST'], strict_slashes=False)
def ai_chat():
    """
    Perform a chat with the AI model using the provided prompt.

    Returns:
    flask.Response: A JSON response containing the AI's response to the provided prompt
    with an HTTP status code 201 if the chat is successful.
    """
    data = request.get_json()
    prompt = data.get('prompt')
    response = chat.send_message(prompt)
    return jsonify({'AI': markdown(response.text)}), 201


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6000, threaded=True)

