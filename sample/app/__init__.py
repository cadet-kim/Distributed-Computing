from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)

app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

app.config['GOOGLE_CLIENT_ID'] = '861514102522-c8vppikutcunjkj8qshqp2f5c76n926s.apps.googleusercontent.com'
app.config['GOOGLE_CLIENT_SECRET'] = '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'
app.config['GOOGLE_DISCOVERY_URL'] = 'https://accounts.google.com/.well-known/openid-configuration'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.login_message = "로그인이 필요한 페이지입니다."

migrate = Migrate(app, db)

oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
    client_kwargs={'scope': 'openid email profile'}
)

from app import routes
from flask_migrate import Migrate
migrate = Migrate(app, db)
from app import models
