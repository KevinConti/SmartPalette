from flask import Flask, jsonify, render_template, Blueprint
from flask import request, flash, redirect, url_for, send_from_directory
from flask import current_app as app
from smartpalette.models.models import db, User
from werkzeug.utils import secure_filename
import os

blue_print = Blueprint('blue_print', __name__, template_folder='templates')

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'tif'])
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.getcwd(), "./uploads"))

def allowed_file(filename):
    return '.' in filename \
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blue_print.route('/users/<string:username>', methods=['GET'])
def get_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_profile.html', user=user)

@blue_print.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        if not request.form['username'] or not request.form['password']:
            flash("Please enter all the fields", 'error')
        else:
            new_user = User(
                request.form['username'],
                request.form['password']
            )

            db.session.add(new_user)
            db.session.commit()
            flash('Registration Successful')
            return redirect(url_for(
                    'blue_print.get_user', 
                    username=request.form['username']
                )
            )
    return render_template('register.html')

@blue_print.route('/uploads', methods=['GET', 'POST'])
def upload():

    if request.method == 'POST':
        image = request.files.get('file')
        if image == None:
            flash('No selected file')
        elif image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    filename
                )
            )
            return redirect(url_for(
                    'blue_print.display',
                    filename=filename
                )
            )
        else:
            flash('Only upload png, jpeg, jpg, and tif.')
    return render_template('upload.html')

@blue_print.route('/uploads/<string:filename>')
def get_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@blue_print.route('/display/<string:filename>', methods=['GET'])
def display(filename):
    filename = 'http://localhost:5000/uploads/' + filename
    return render_template('display.html', filename=filename)