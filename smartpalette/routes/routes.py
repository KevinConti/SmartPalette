from smartpalette.Algorithm.ColorPaletteGenerator import PaletteGenerator
from smartpalette.routes.api import API_ENDPOINT
from smartpalette.models.models import User
from flask import Flask, render_template, Blueprint
from flask import request, flash, redirect, url_for, send_from_directory
from flask_login import current_user, login_user, logout_user
from flask import current_app as app
from werkzeug.utils import secure_filename
from uuid import uuid4

import requests
import os

MODE = "development"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'tif'])
GENERATOR = PaletteGenerator()

if MODE == "development":
    URL = "http://localhost:5000"
    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.getcwd(), "./uploads"))
else:
    URL = "https://smartpalette.herokuapp.com"
    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.getcwd(), "./smartpalette/uploads"))

blue_print = Blueprint('blue_print', __name__, template_folder='templates')

def allowed_file(filename):
    return '.' in filename \
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blue_print.route('/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == "POST":
        if not request.form['username'] or not request.form['password']:
            flash("Please enter all the fields", 'error')
        else:
            user_data = {}
            user_data['username'] = request.form['username']
            user_data['password'] = request.form['password']

            r = requests.post(URL + API_ENDPOINT + "/users/", json=user_data)

            return redirect(url_for(
                    'blue_print.profile', 
                    username=request.form['username']
                )
            )
    return render_template('register.html')

@blue_print.route('/profile/<string:username>', methods=['GET'])
def profile(username):
    try:
        user = requests.get(URL + API_ENDPOINT + "/users/{}".format(username)).json()
    except ValueError:
        return 'Sorry, this user does not exist'
    return render_template('profile.html', username=user.get('username'), images=user.get('images'))

@blue_print.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        if not request.form.get('username') or not request.form.get('password'):
            flash("Error: Please enter your username and password")
        else:
            user = User.query.filter_by(username=request.form['username']).first()
            if user is None or not user.check_password(request.form['password']):
                flash('Invalid username or password')
                return redirect(url_for('blue_print.login'))
            else:
                login_user(user)
                return redirect(url_for('index'))
    return render_template('login.html')

@blue_print.route('/logout/')
def logout():
    if current_user.is_authenticated:
        logout_user()
        return redirect(url_for('index'))
    else:
        return redirect(url_for('blue_print.login'))

@blue_print.route('/upload/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        image = request.files.get('file')

        #Error handling needs to exist for num_of_colors
        num_of_colors = int(request.form.get('color_num'))
        if image == None:
            flash('Invalid input. Please upload a proper image type and number of colors.')
        elif image and allowed_file(image.filename):
            filename = secure_filename(str(uuid4()))
            image.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    filename
                )
            )
            color_list = GENERATOR.create_palette(image, num_of_colors)

            if current_user.is_authenticated:
                rgb_colors = {}
                for i in color_list:
                    rgb_colors = {}
                    rgb_colors['r'] = i[0]
                    rgb_colors['g'] = i[1]
                    rgb_colors['b'] = i[2]
                    requests.post(URL + API_ENDPOINT + '/colors/', json=rgb_colors)

            return redirect(url_for(
                    'blue_print.display',
                    filename=filename
                )
            )
        else:
            flash('Only upload png, jpeg, jpg, and tif.')
    return render_template('upload.html')

@blue_print.route('/display/<string:filename>', methods=['GET'])
def display(filename):
    filename = URL + API_ENDPOINT + '/images/' + filename
    return render_template('display.html', filename=filename)
