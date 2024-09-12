from flask import Flask, make_response, jsonify, request, abort, session
from flask_mongoalchemy import MongoAlchemy
import logging
from flask_cors import CORS
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash

# Flask app initialization
app = Flask(__name__)
CORS(app)

# MongoAlchemy configuration
app.config['MONGOALCHEMY_DATABASE'] = 'flask_db'
app.config['MONGOALCHEMY_CONNECTION_STRING'] = 'mongodb://mongodb:27017/flask_db'

# MongoAlchemy initialization
db = MongoAlchemy(app)

# Logging setup
logging.basicConfig()
logging.getLogger('mongoalchemy').setLevel(logging.INFO)

# User model
class User(db.Document, UserMixin):
    username = db.StringField(max_length=20)
    password_hash = db.StringField(max_length=80)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Notes model
class Notes(db.Document):
    title = db.StringField(max_length=45)
    content = db.StringField()
    created_at = db.DateTimeField()
    updated_at = db.DateTimeField()

    def save(self, *args, **kwargs):
        self.updated_at = db.func.current_timestamp()
        if not self.created_at:
            self.created_at = db.func.current_timestamp()
        super(Notes, self).save(*args, **kwargs)

# Registration form
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=25)],
                           render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=25)],
                           render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")
    
    def validate_username(self, username):
        existing_user = User.query.filter(User.username == username.data).first()
        if existing_user:
            raise ValidationError('Username already exists!')

# Login form
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=25)],
                           render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=25)],
                           render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")

# Register route
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if User.query.filter(User.username == username).first():
        return jsonify({'message': 'User already exists'}), 400

    new_user = User(username=username)
    new_user.set_password(password)
    new_user.save()

    return jsonify({'message': 'User registered successfully'})

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter(User.username == username).first()

    if user and user.check_password(password):
        session['user_id'] = user.mongo_id
        return jsonify({'message': 'Login successful'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200

# Get all notes
@app.route('/notes', methods=['GET'], strict_slashes=False)
def get_all_notes():
    all_notes = Notes.query.all()
    notes_list = [{'notes_id': note.mongo_id, 'title': note.title, 'content': note.content,
                   'created_at': note.created_at, 'updated_at': note.updated_at} for note in all_notes]
    return jsonify(notes_list), 200

# Get note by ID
@app.route('/notes/<int:id>', methods=['GET'], strict_slashes=False)
def get_notes_id(id):
    note = Notes.query.filter(Notes.mongo_id == id).first()
    if note:
        return jsonify({
            'notes_id': note.mongo_id,
            'title': note.title,
            'content': note.content,
            'created_at': note.created_at,
            'updated_at': note.updated_at
        }), 200
    else:
        return abort(404)

# Add note
@app.route('/notes', methods=['POST'], strict_slashes=False)
def add_note():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    new_note = Notes(title=title, content=content)
    new_note.save()
    return jsonify({'message': 'Note added successfully!'}), 201

# Delete note
@app.route('/notes/<int:id>', methods=['DELETE'], strict_slashes=False)
def delete_note(id):
    note = Notes.query.filter(Notes.mongo_id == id).first()
    if note:
        note.remove()
        return jsonify({'message': 'Note deleted successfully!'}), 200
    else:
        return abort(404)

# Update note
@app.route('/notes/<int:id>', methods=['PUT'], strict_slashes=False)
def update_note(id):
    note = Notes.query.filter(Notes.mongo_id == id).first()
    if note:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        note.title = title
        note.content = content
        note.save()
        return jsonify({'message': 'Note updated successfully!'}), 200
    return abort(404)

if _name_ == "_main_":
    app.run(host='0.0.0.0', port=6000, threaded=True)
