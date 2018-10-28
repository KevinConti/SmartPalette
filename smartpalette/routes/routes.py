from flask import Blueprint, render_template
from smartpalette.models.models import *
from flask_restful import Resource, Api


smart_palette = Blueprint("smartpalette", __name__)

@smart_palette.route("/users/<username>")
def users(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_profile.html', user=user)