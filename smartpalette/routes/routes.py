from flask import Flask, jsonify, render_template, Blueprint
from smartpalette.models.models import User

blue_print = Blueprint('blue_print', __name__, template_folder='templates')

@blue_print.route('/users/<string:username>', methods=['GET'])
def get_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_profile.html', user=user)