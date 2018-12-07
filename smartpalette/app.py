import os

from flask import Flask, render_template
from flask_migrate import Migrate

from smartpalette.models.models import db, User
from smartpalette.routes.routes import blue_print
from smartpalette.routes.api import api
from flask_login import LoginManager

login = None

#Note: Use FLASK_ENV=development for local dev (with local postgres)
def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    # If an environment was manually requested, set to that environment regardless of cli request
    # Mostly used for pytest
    # if env:
    #     app.env = env
    app = configure_app(app)
    app.register_blueprint(blue_print)
    app.register_blueprint(api)
    db.init_app(app)

    migrate = Migrate(app, db)

    login = LoginManager(app)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @login.user_loader
    def load_user(username):
        return User.query.get(username)

    # a simple page that says hello
    @app.route('/', methods=['GET', 'POST'])
    def index():
        return render_template('index.html')

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    return app


def configure_app(app):
    import os

    # Connects to the appropriate database according to the DB_CONN variable
    # If "Development" then will attempt to find a local postgresql DB
    # Else will attempt to connect to prod
    app.config['SECRET_KEY'] = "abcitseasyas123"
    if (app.env == "development"):
        # If this doesn't work, go to psql shell and run "delete from alembic_version;"
        """
        For the user name and password, set environmental variables
        PGUSER = postgres
        PGPASSWORD = your password that you set for the postgres installation
        """
        try:
            username = os.environ['PGUSER']
            password = os.environ['PGPASSWORD']
        except KeyError:
            # Tries to use defaults if environment variables aren't set.
            username = 'postgres'
            password = 'password'

        app.config['UPLOAD_FOLDER'] = os.path.abspath(os.path.join(os.getcwd(), "./smartpalette/uploads"))

        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://{}:{}@localhost:5432/local_database'.format(
            username,
            password
        )

        # For migrations, use below app.config instead of above:
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://{}:{}@localhost:5432/prod_copy'.format(
        #     username,
        #     password
        # )

        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
        print("loaded local_database to app")
    elif (app.env == "production"):
        app.config['UPLOAD_FOLDER'] = os.path.abspath(os.path.join(os.getcwd(), "./smartpalette/uploads"))
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    elif (app.env == "testing"):
        print("Setting up connection to 'test_local_database'")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:password@localhost:5432/test_local_database'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    else:
        print("Warning: Application is not running in either development or production mode")
        print("Defaulting to development mode")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://localhost/local_database'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    return app
