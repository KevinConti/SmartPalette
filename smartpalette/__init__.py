import os

from flask import Flask, render_template
from smartpalette.routes.routes import smart_palette

username = os.environ['PGUSER']
password = os.environ['PGPASSWORD']


#Note: Use FLASK_ENV=Development for local dev (with local postgres)
def create_app(env=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    # If an environment was manually requested, set to that environment regardless of cli request
    # Mostly used for pytest
    if env:
        app.env = env
    app = configure_app(app)
    # init database
    from smartpalette.models.models import db, User

    db.init_app(app)

    #USE THIS BLOCK TO CREATE A LOCAL DATABASE THAT MAPS TO MODELS
    with app.app_context():
        db.init_app(app)

        db.create_all()
        db.session.commit()

        jacob = User('jacob', 'password')
        db.session.add(jacob)
        db.session.delete(jacob)
        db.session.commit()


    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.register_blueprint(smart_palette)

    # a simple page that says hello
    @app.route('/')
    def hello():
        return render_template('hello_template.html')

    return app


def configure_app(app):
    import os

    # Connects to the appropriate database according to the DB_CONN variable
    # If "Development" then will attempt to find a local postgresql DB
    # Else will attempt to connect to prod
    if (app.env == "development"):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://{}:{}@localhost:5432/mylocaldb'.format(username, password)
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
        print("loaded local_database to app")
    elif (app.env == "production"):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    elif (app.env == "testing"):
        print("Setting up connection to 'test_local_database'")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:password@localhost:5432/test_local_database'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    else:
        print("Warning: Application is not runnign in either development or production mode")
        print("Defaulting to development mode")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://localhost/local_database'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    return app