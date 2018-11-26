from flask import Flask, render_template, Blueprint
from flask import request, flash, redirect, url_for, send_from_directory
from flask_login import current_user, login_user, logout_user
from flask import current_app as app
from smartpalette.models.models import db, User, Palette, Color
from smartpalette.Algorithm.ColorPaletteGenerator import PaletteGenerator
from werkzeug.utils import secure_filename

import requests
import json
import os

mode = "prod"

if mode == "development":
    URL = "http://localhost:5000"
    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.getcwd(), "./uploads"))
else:
    URL = "https://smartpalette.herokuapp.com"
    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.getcwd(), "./smartpalette/uploads"))

blue_print = Blueprint('blue_print', __name__, template_folder='templates')

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'tif'])

GENERATOR = PaletteGenerator()

def allowed_file(filename):
    return '.' in filename \
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blue_print.route('/users/<string:username>', methods=['GET'])
def get_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_profile.html', user=user)

@blue_print.route('/users/', methods=['POST'])
def create_user():
    data = request.get_json()
    new_user = User(data['username'], data['password'])
    db.session.add(new_user)
    db.session.commit()
    return "Added user {}".format(data['username'])

@blue_print.route('/images/<string:filename>')
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@blue_print.route('/images/', methods=['POST'])
def create_image():
    # TODO: Create an image in the context of a user
    pass

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

            r = requests.post(URL+"/users/", json=user_data)

            return redirect(url_for(
                    'blue_print.get_user', 
                    username=request.form['username']
                )
            )
    return render_template('register.html')

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
            filename = secure_filename(image.filename)
            image.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    filename
                )
            )
            color_list = GENERATOR.create_palette(image, num_of_colors)
            print(color_list) # this works, now I just need to create a image for the db + colors
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
    filename = URL + '/images/' + filename
    return render_template('display.html', filename=filename)
