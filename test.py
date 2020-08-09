from flask import Flask
from flask import Flask, flash, redirect, render_template,url_for, request, session, abort
from flask_mysqldb import MySQL
from wtforms import Form, BooleanField, SubmitField, StringField , TextAreaField ,PasswordField , validators
from wtforms.validators import Required
from flask_wtf import Form
from wtforms import TextField, BooleanField
import MySQLdb
import re
from functools import wraps
import MySQLdb.cursors
from flask_bootstrap import Bootstrap
...

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.secret_key = "secret key"

#config MySQL
app.config['MySQL_USER'] = 'root'
app.config['MySQL_PASSWORD'] = ''
app.config['MySQL_HOST'] = 'localhost'
app.config['MySQL_DB'] = 'webapp'

#init MySQL_USER
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template("index.html")

class LoginForm(Form):
    username = StringField()
    password = PasswordField()
    submit = SubmitField('Sign In')

@app.route('/index', methods=['GET', 'POST'])
def login():
    e = none
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
    #if request.method == 'POST' and form.validate():
    #    username.form = request.form ['username']
    #    password.form = request.form['password']
        try:
            dcn, cur = get_connection()
            cursor.execute('SELECT * FROM webapp.login_details WHERE username = %s AND password = %s',(username, password))
            if login_details:
                session['logged_in'] = True
                session['STU'] = True
                session['username'] = login_details['username']
                #user1 = login_details.upper()

                return redirect('/login')#login_details=user1
            #else:
            #    e = "Invalid Credential"
            #    return render_template('/index')

        except (MySQLdb.Error, MySQLdb.Warning) as e:
            return render_template('login.html',title = 'Sign In', error=e, form=form)

def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
         if 'logged_in' in session:
             return test(*args, **kwargs)
         else:
             flash('You need to login first')
             return redirect(url_for('index'))
    return wrap


@app.route('/home')
def home():
     # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
