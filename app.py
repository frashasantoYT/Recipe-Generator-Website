from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators
from wtforms.validators import DataRequired, Email, EqualTo
import sqlite3

from flask_mail import Mail, Message
import os
import secrets


app = Flask(__name__)

app.config['SECRET_KEY'] = '53a4737f02e21ed27eb0d0fa5ecc2669'


def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY,
                 username TEXT NOT NULL,
                 email TEXT NOT NULL,
                 password TEXT NOT NULL,
                 reset_token TEXT)''') 
    conn.commit()
    conn.close()

    
    
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jackmutiso37@gmail.com'
app.config['MAIL_PASSWORD'] = 'ttatlmondgtomozz'
app.config['MAIL_DEFAULT_SENDER'] = 'jackmutiso37@gmail.com'
mail = Mail(app)


def generate_reset_token():
    return secrets.token_urlsafe(16)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        if user:
          
            reset_token = generate_reset_token()
            
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("UPDATE users SET reset_token = ? WHERE email = ?", (reset_token, email))
            conn.commit()
            conn.close()
            
            send_reset_email(email, reset_token)
            return render_template('forgot_password_success.html')
        else:
            return render_template('forgot_password.html', form=form, message='Email not found')
    return render_template('forgot_password.html', form=form)


def send_reset_email(email, reset_token):
    token_link = url_for('reset_password', token=reset_token, _external=True)
    msg = Message('Password Reset Request', recipients=[email])
    msg.body = f'''To reset your password, click the following link:
{token_link}

If you did not make this request, simply ignore this email.
'''
    mail.send(msg)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = ResetPasswordForm()
    if form.validate_on_submit():
        password = form.password.data
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE reset_token = ?", (token,))
        user = c.fetchone()
        if user:
            # Update user's password and reset_token fields
            c.execute("UPDATE users SET password = ?, reset_token = NULL WHERE reset_token = ?", (password, token))
            conn.commit()
            conn.close()
            return render_template('reset_password_success.html')
        else:
            conn.close()
            return render_template('reset_password.html', form=form, token=token, message='Invalid or expired token')
    return render_template('reset_password.html', form=form, token=token)


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


# Load recipes from recipes.txt
def load_recipes():
    with open('recipes.txt', 'r') as file:
        recipes = file.read().split('\n\n')  # Split recipes by empty lines
    return recipes

recipes = load_recipes()


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


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
            return redirect(url_for('home'))
        else:
            # Invalid credentials
            return render_template('login.html', form=form, message='Invalid email or password')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('email', None)  # Clear the 'email' key from the session
    return redirect(url_for('login'))


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
    search_query = request.form.get('search_query').lower()
    matched_recipes = [recipe for recipe in recipes if search_query in recipe.lower()]
    return jsonify({'recipes': matched_recipes})


if __name__ == '__main__':
    init_db()  # Initialize database
    app.run(debug=True)
   
