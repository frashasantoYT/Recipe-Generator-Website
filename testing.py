from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators
from wtforms.validators import DataRequired, Email, EqualTo
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Database initialization
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY,
                 username TEXT NOT NULL,
                 email TEXT NOT NULL,
                 password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# Load recipes from recipes.txt
def load_recipes():
    with open('recipes.txt', 'r') as file:
        recipes = file.read().split('\n\n')  # Split recipes by empty lines
    return recipes

recipes = load_recipes()

# User registration form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

# User login form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Routes
@app.route('/')
def home():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('main.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = c.fetchone()
        conn.close()
        if user:
            # Login successful
            session['email'] = email
            return redirect(url_for('recipe'))
        else:
            # Invalid credentials
            return render_template('login.html', form=form, message='Invalid email or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/recipe')
def recipe():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/search_recipe', methods=['POST'])
def search_recipe():
    if 'email' not in session:
        return redirect(url_for('login'))
    search_query = request.form.get('search_query').lower()
    matched_recipes = []

    with open('recipes.txt', 'r') as file:
        recipes_text = file.read().split('\n\n')  # Split recipes by double newline characters
        
        for recipe_text in recipes_text:
            title = recipe_text.split('\n')[0].lower()  # Extracting the title from the recipe text
            
            if search_query in title:
                matched_recipes.append(recipe_text)

    return jsonify({'recipes': matched_recipes})

if __name__ == '__main__':
    init_db()  # Initialize database
    app.run(debug=True)
