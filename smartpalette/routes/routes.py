from smartpalette.Algorithm.ColorPaletteGenerator import PaletteGenerator
from smartpalette.models.models import User, Color, Palette, db
from flask import Flask, render_template, Blueprint, abort, jsonify
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
import smartpalette.routes.api as api

API_ENDPOINT = "api/v1"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'tif'])
GENERATOR = PaletteGenerator()

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

            r = requests.post(request.url_root + API_ENDPOINT + "/users/", json=user_data)

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
        user = requests.get(request.url_root + API_ENDPOINT + "/users/{}".format(username)).json()
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
                new_image = api.create_image({"filename":filename, "username":current_user.username})
                new_palette = Palette(new_image)
                rgb_colors = {}
                for i in color_list:
                    rgb_colors = {}
                    rgb_colors['r'] = i[0]
                    rgb_colors['g'] = i[1]
                    rgb_colors['b'] = i[2]
                    new_color = api.create_color(rgb_colors)
                    new_palette.colors.append(new_color)
                new_palette.image = new_image
                db.session.add(new_palette)
                db.session.commit()
            else:
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
    image = request.url_root + API_ENDPOINT + '/images/' + filename
    return render_template('display.html', filename=image)

@blue_print.route('/browse', methods=['GET', 'POST'])
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
@blue_print.route('/funfacts', methods=['GET', 'POST'])
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
    result = connection.execute(sql, keyword='%awesome%')

    # There will only be one row and one column, which will be the count of users, so grab that:
    for row in result:
        numAwesome = row[0]

    # Query 6: Stored procedure that is subsequently called and determines the total # of palettes

    # Below commented line is for debugging only
    # connection.execute('DROP FUNCTION numPal;')

    connection.execute("CREATE OR REPLACE FUNCTION numPal() "
                        "RETURNS bigint AS $numPal$ "
                        "SELECT COUNT(*) FROM palette;"
                        "$numPal$ "
                        "LANGUAGE SQL;")

    result = connection.execute("SELECT * FROM numPal();")
    # There will only be one row and one column, which will be the count of users, so grab that:
    for row in result:
        numPalettes = row[0]

    # Query 7: Stored Procedure that returns a trigger and increments the visited counter
    # This is launched by a trigger (See Query 8)

    # Below commented line is for debugging only
    # connection.execute('DROP FUNCTION increment();')

    connection.execute('CREATE OR REPLACE FUNCTION increment() '
                       'RETURNS TRIGGER AS $k$ '
                       'BEGIN '
                       'UPDATE count SET "currentCount" = "currentCount" + 1; '
                       'RETURN NEW; '
                       'END; '
                       '$k$ '
                       'LANGUAGE plpgsql;')

    # Query 8.5: There is no 'CREATE OR REPLACE' for triggers,
    # So we must drop if it exists
    connection.execute('DROP TRIGGER IF EXISTS k ON count;')

    # Query 8: Establishes a Trigger that updates count.num on a INSERT request for the count
    connection.execute('CREATE TRIGGER k AFTER INSERT '
                       'ON count '
                       'FOR EACH ROW EXECUTE PROCEDURE increment();')

    # Query 9: Add an index to the count table, which triggers the trigger
    connection.execute('INSERT INTO count VALUES(0);')

    # Query 10: Get the max count
    result = connection.execute('SELECT MAX("currentCount") FROM count ')
    # There will only be one row and one column, which will be the count of users, so grab that:
    for row in result:
        visited = row[0]

    connection.close()
    return render_template('funfacts.html',
                           numUsers=count,
                           powerUsers=powerUsers,
                           numAwesome=numAwesome,
                           numPalettes=numPalettes,
                           visited=visited)


# Setup connection to DB in order to manually write queries to comply with CSC 455 requirements
def setup_database_connection():
    with app.app_context():
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    connection = engine.connect()
    return connection
