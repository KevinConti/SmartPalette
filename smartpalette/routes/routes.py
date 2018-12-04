from smartpalette.Algorithm.ColorPaletteGenerator import PaletteGenerator
from smartpalette.routes.api import API_ENDPOINT
from smartpalette.models.models import User
from flask import Flask, render_template, Blueprint, abort
from flask import request, flash, redirect, url_for, send_from_directory
from flask_login import current_user, login_user, logout_user
from flask import current_app as app
from werkzeug.utils import secure_filename
from uuid import uuid4

# For requests to DB
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

import requests
import os

MODE = "development"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'tif'])
GENERATOR = PaletteGenerator()
ANON_COLORS = []

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
    """ 
    ERROR HANDLING TO DO: 
    - username is all alpha & numeric characters
    - username is at least 3 characters
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == "POST":
        if not request.form['username'] or not request.form['password']:
            flash("Please enter all the fields")
        else:
            user_data = {}
            user_data['username'] = request.form['username']
            user_data['password'] = request.form['password']

            r = requests.post(URL + API_ENDPOINT + "/users/", json=user_data)

            if r.status_code == 409:
                flash("User already exists, please try again.")
            else:
                return redirect(url_for(
                        'blue_print.profile', 
                        username=request.form['username']
                    )
                )
    return render_template('register.html')

@blue_print.route('/profile/<string:username>', methods=['GET'])
def profile(username):
    username = username.lower()
    try:
        user = requests.get(URL + API_ENDPOINT + "/users/{}".format(username)).json()
    except ValueError:
        return 'Sorry, this user does not exist'
    return render_template('profile.html', username=username.capitalize(), images=user.get('images'))

@blue_print.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        if not request.form.get('username') or not request.form.get('password'):
            flash("Error: Please enter your username and password")
        else:
            user_name = request.form['username'].lower()
            user = User.query.filter_by(username=user_name).first()
            if user is None or not user.check_password(request.form['password']):
                flash('Error: Invalid username or password')
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

        # Error handling needs to exist for num_of_colors != alphacharacters, 0, < 10, etc.
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
            else:
                ANON_COLORS.append((filename, color_list))

                return redirect(url_for(
                        'blue_print.display',
                        filename=filename
                    )
                )
        else:
            flash('Only upload png, jpeg, jpg, and tif.')
    return render_template('upload.html')

@blue_print.route('/display/<string:filename>/', methods=['GET'])
def display(filename):
    try:
        # Ran a 4 loop in case there were multiple users uploading at the same time
        for i in ANON_COLORS:
            if i[0] == filename:
                tup = i
        colors = tup[1]
        ANON_COLORS.remove(tup)
        image = URL + API_ENDPOINT + '/images/' + filename
    except UnboundLocalError:
        abort(404)
    return render_template('display.html', filename=image, color_list=colors)

@blue_print.route('/browse')
def browse():
    connection = setup_database_connection()

    # Query 1: Two-table self-join to find every color in each palette
    listOfTuples = get_color_tuples(connection);

    # Query 2: Three-table join (palette, user, image)
    palettesById = get_palettes_by_id(connection)


    connection.close()
    return render_template('browse.html', paletteColors=listOfTuples, palettesById=palettesById)


def get_color_tuples(connection):
    result = connection.execute('SELECT DISTINCT p1."paletteId", p1.hex FROM palette_colors p1 '
                                'INNER JOIN palette_colors p2 on p1."paletteId" = p2."paletteId" '
                                'AND p1.hex <> p2.hex;');

    # Format the ResultQuery into a list of dictionaries
    paletteColors = []
    for row in result:
        thisdict = {
            "paletteId": row[0],
            "hex": row[1]
        }
        paletteColors.append(thisdict)

    # Translate the list of dictionaries into a dictionary of tuples
    # No, I'm not this smart. Here's the SO link:
    # https://stackoverflow.com/questions/15917319/convert-a-list-of-dictionaries-into-a-dictionary-of-tuples
    from collections import defaultdict
    dict_of_touples = defaultdict(tuple)

    for dct in paletteColors:
        dict_of_touples[dct['paletteId']] += (dct['hex'],)

    # Order it
    from collections import OrderedDict
    sortedTouples = OrderedDict(sorted(dict_of_touples.items()))

    return sortedTouples


def get_palettes_by_id(connection):
    sql = text('SELECT palette."paletteId", filepath, "user".username '
               'FROM palette '
               'INNER JOIN image on palette."paletteId" = image."paletteId" '
               'INNER JOIN "user" on image.username = "user".username '
               'ORDER BY palette."paletteId";')
    result = connection.execute(sql)

    palettesById = []
    for row in result:
        thisdict = {
            "paletteId": row[0],
            "filepath": row[1],
            "username": row[2],
        }
        palettesById.append(thisdict)

    return palettesById


# This route displays various 'fun facts' about the website, such as the number of users and such
# Primarily intended to meet user requirements for user: CSC 455
@blue_print.route('/funfacts')
def funfacts():
    connection = setup_database_connection()

    # Query 3: Aggregate function to find the total number of users who have signed up
    result = connection.execute('SELECT COUNT(*) from "user";');

    # There will only be one row and one column, which will be the count of users, so grab that:
    for row in result:
        count = row[0]

    # Query 4: Aggegrate function using GROUP BY and HAVING, which finds our 'power users' (> 5 palettes)
    result = connection.execute('SELECT COUNT(i."paletteId") as "Number of Palettes", "user".username from "user" '
                                'INNER JOIN image i on "user".username = i.username '
                                'INNER JOIN palette p on i."paletteId" = p."paletteId" '
                                'GROUP BY "user".username '
                                'HAVING COUNT(i."paletteId") > 5;')

    powerUsers = []
    for row in result:
        print("row:", row)
        thisdict = {
            "numPalettes": row[0],
            "username": row[1]
        }
        powerUsers.append(thisdict)

    # Query 5: Text-based search query using "LIKE" and Wildcards, which finds the number of "awesome" uploads
    # Note that we need to use sqlAlchemy.text() in order to properly create this query due to the "like" keyword
    sql = text("SELECT COUNT(filepath) FROM image WHERE filepath LIKE :keyword;")
    result = connection.execute(sql, keyword='%awesome%');

    # There will only be one row and one column, which will be the count of users, so grab that:
    for row in result:
        numAwesome = row[0]

    connection.close()
    return render_template('funfacts.html', numUsers=count, powerUsers=powerUsers, numAwesome=numAwesome)


# Setup connection to DB in order to manually write queries to comply with CSC 455 requirements
def setup_database_connection():
    with app.app_context():
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    connection = engine.connect()
    return connection
