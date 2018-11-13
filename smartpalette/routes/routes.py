from flask import Flask, jsonify, render_template, Blueprint
from flask import request, flash, redirect, url_for
from smartpalette.models.models import db, User

blue_print = Blueprint('blue_print', __name__, template_folder='templates')

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

@blue_print.route('/upload', methods=['GET', 'POST'])
def upload():
    # TODO
    return render_template('upload.html')