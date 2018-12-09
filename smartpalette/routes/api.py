from flask import request, jsonify, Blueprint, send_from_directory, abort
from flask import current_app as app
import smartpalette.models.models as models # db, User, Palette, Color
import werkzeug.exceptions as ex
import os

api = Blueprint('api', __name__, template_folder='templates')
API_ENDPOINT = "/api/v1"

@api.route(API_ENDPOINT + '/users/<string:username>', methods=['GET'])
def get_user(username):
    """
    An api method to return the username and user images given 
    a specific username
    """
    user = models.User.query.filter_by(username=username).first_or_404()
    user_images = [str(img) for img in user.images]
    return jsonify(username=user.username, images=user_images)

@api.route(API_ENDPOINT + '/users/', methods=['POST'])
def create_user():
    """
    An api method to create users in the database
    """
    data = request.get_json()
    if models.User.is_username_taken(data['username']):
        return jsonify('User already exists'), 409
    else:
        new_user = models.User(data['username'].lower(), data['password'])
        models.db.session.add(new_user)
        models.db.session.commit()
    return "Added user {}".format(data['username'])

def get_image_object(filename):
    """
    Returns an image object for a specific filename
    """
    return models.Image.query.filter_by(filepath=filename).first_or_404()

def get_palette_object(id):
    """
    Returns a palette object for a specific paletteId
    """
    return models.Palette.query.filter_by(paletteId=id).first_or_404()

@api.route(API_ENDPOINT + '/images/<string:filename>')
def get_image(filename):
    """
    An api method to get a specific image given the filename
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@api.route(API_ENDPOINT + '/images/<string:filename>', methods=['DELETE'])
def delete_image(filename):
    """
    An api method to delete an image in the directory
    """
    os.remove(app.config['UPLOAD_FOLDER'] + '/' + filename)
    return "Deleted image"

def create_image(data):
    """
    Creates a new image and returns it
    """
    user = models.User.query.filter_by(username=data['username']).first_or_404()
    new_image = models.Image(data['filename'], user)
    models.db.session.add(new_image)
    models.db.session.commit()
    return new_image

@api.route(API_ENDPOINT + '/colors/<string:hex>', methods=['GET'])
def get_color(hex):
    """
    An api method to get a color's values by provided a hex code
    """
    color = models.Color.query.filter_by(hex=hex).first_or_404()
    return jsonify(hex=color.hex, rgb=[color.rValue, color.gValue, color.bValue])

def create_color(data):
    """
    Creates and returns a new color. If the color already exists in the 
    database, then it will return a reference to the database object
    """
    try:
        new_color = models.Color(data['r'], data['g'], data['b'])
        models.db.session.add(new_color)
        models.db.session.commit()
    except Exception:
        models.db.session.rollback()
        hex = models.Color.rgb2hex(data['r'], data['g'], data['b'])
        return models.Color.query.filter_by(hex=hex).first_or_404()
    return new_color
