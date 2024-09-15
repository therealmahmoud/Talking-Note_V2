from flask import Flask, make_response, jsonify, request, abort, render_template, url_for, redirect, session
from flask_pymongo import PyMongo
import logging
from flask_cors import CORS
from datetime import datetime, timedelta
import google.generativeai as genai
from markdown import markdown
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os

genai.configure(api_key='AIzaSyDCKpjPKsWbDdlBtnQItbSwxkeHlSUqefE')  # api key for AI model
model = genai.GenerativeModel('gemini-1.5-flash') # assign default model
chat = model.start_chat(history=[]) # create chat history
app = Flask(__name__) # Flask
app.config['SECRET_KEY'] = "hamada"

app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # 1 hour

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

# MongoDB config
app.config['MONGO_URI'] = 'mongodb://root:root_password@mongodb:27017/flask_db?authSource=admin'
logging.basicConfig()  # logging
mongo = PyMongo(app)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': "Not found"}), 404)


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=25)],
                           render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=25)],
                           render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user = mongo.db.users.find_one({"username": username.data})
        if existing_user:
            raise ValidationError('Username already exists!')

# Login form
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=25)],
                           render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=25)],
                           render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")


@app.route('/register', methods=['POST'])
def register():
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
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = mongo.db.users.find_one({'username': username})

    if user and check_password_hash(user['password'], password):
        session['user_id'] = str(user['_id'])
        print(f"session user_id {session['user_id']} and _id {str(user['_id'])}")
        return jsonify({'message': 'Login successful'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200

# Get all notes
@app.route('/notes', methods=['GET'], strict_slashes=False)
def get_all_notes():
    all_notes = mongo.db.notes.find()
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


#not completed
@app.route('/notes/<string:id>', methods=['GET'], strict_slashes=False)
def get_notes_id(id):
    note = mongo.db.notes.find_one({'_id': ObjectId(id)})
    if note:
        return jsonify({
            'notes_id': str(note['_id']),
            'title': note['title'],
            'content': note['content'],
            'created_at': note['created_at'],
            'updated_at': note['updated_at']
        }), 200
    else:
        return abort(404)

# Add note
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
    print(f"this is user_id from note {new_note['user_id']}")
    mongo.db.notes.insert_one(new_note)
    return jsonify({'message': 'Note added successfully!'}), 201


@app.route('/notes/<string:id>', methods=['DELETE'], strict_slashes=False)
def delete_note(id):
    note = mongo.db.notes.find_one({'_id': ObjectId(id)})
    if note:
        mongo.db.notes.delete_one({'_id': ObjectId(id)})
        return jsonify({'message': 'Note deleted successfully!'}), 200
    else:
        return abort(404)

#not completed
@app.route('/notes/<string:id>', methods=['PUT'], strict_slashes=False)
def update_note(id):
    note = mongo.db.notes.find_one({'_id': ObjectId(id)})
    if note:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')

        mongo.db.notes.update_one({'_id': ObjectId(id)}, {
            '$set': {
                'title': title,
                'content': content,
                'updated_at': mongo.db.func.current_timestamp()
            }
        })
        return jsonify({'message': 'Note updated successfully!'}), 200
    return abort(404)


@app.route('/notes/ai', methods=['POST'], strict_slashes=False)
def ai_chat():
    data = request.get_json()
    prompt = data.get('prompt')
    response = chat.send_message(prompt)
    return jsonify({'AI': markdown(response.text)}), 201


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6000, threaded=True)
