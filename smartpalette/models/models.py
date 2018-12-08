from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from smartpalette import app

db = SQLAlchemy()

class User(UserMixin, db.Model):
    username = db.Column(db.String(), primary_key=True)
    password = db.Column(db.String(120))
    images = db.relationship('Image', backref='user', lazy=True)

    def __repr__(self):
        return '<user: {}>'.format(self.username)

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def get_id(self):
        return self.username

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @classmethod
    def is_username_taken(cls, username):
        return db.session.query(db.exists().where(User.username==username)).scalar()

class Image(db.Model):
    filepath = db.Column(db.String(), primary_key=True)
    username = db.Column(db.String(), db.ForeignKey('user.username'), nullable=False)
    paletteId = db.Column(db.Integer, db.ForeignKey('palette.paletteId'), nullable=True)

    def __init__(self, filename, username, paletteId=None):
        self.filepath = filename
        self.username = username.username
        self.paletteId = paletteId

    def __repr__(self):
        return '{}'.format(self.filepath)

    palette_colors = db.Table(
        'palette_colors',
        db.Column('paletteId', db.Integer, db.ForeignKey('palette.paletteId'), primary_key=True),
        db.Column('hex', db.String(), db.ForeignKey('color.hex'), primary_key=True)
    )


class Palette(db.Model):
    paletteId = db.Column(db.Integer, autoincrement=True, primary_key=True)
    image = db.relationship('Image', backref='image', uselist=False)
    colors = db.relationship('Color', secondary=Image.palette_colors, lazy='subquery',
                             backref=db.backref('palettes', lazy=True))

    def __init__(self, image):
        self.image = image

    def __repr__(self):
        return '<paletteId: {}>'.format(self.paletteId)


class Color(db.Model):
    hex = db.Column(db.String(), primary_key=True)
    rValue = db.Column(db.Integer, nullable=False)
    gValue = db.Column(db.Integer, nullable=False)
    bValue = db.Column(db.Integer, nullable=False)

    def __init__(self, r, g, b):
        self.rValue = r
        self.gValue = g
        self.bValue = b
        self.hex = Color.rgb2hex(r, g, b)

    @staticmethod
    def rgb2hex(r, g, b):
        hex = "{:02x}{:02x}{:02x}".format(r,g,b)
        print(hex)
        return hex

    def __repr__(self):
        return '<Hex value: {}>'.format(self.hex)


class Count(db.Model):
    # Used exclusively for CSC 455 requirement
    currentCount = db.Column(db.Integer, primary_key=True, unique=False, nullable=True)

    def __init__(self, num):
        self.num = num
