from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from werkzeug.middleware.proxy_fix import ProxyFix

import os

app = Flask(__name__)

app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['GOOGLE_CLIENT_ID'] = '861514102522-c8vppikutcunjkj8qshqp2f5c76n926s.apps.googleusercontent.com'
app.config['GOOGLE_CLIENT_SECRET'] = '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'
app.config['GOOGLE_DISCOVERY_URL'] = 'https://accounts.google.com/.well-known/openid-configuration'
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

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
    api_base_url='https://www.googleapis.com/oauth2/v3/',
    client_kwargs={'scope': 'openid email profile'}
)

from app import routes
from flask_migrate import Migrate
migrate = Migrate(app, db)
from app import models


def create_database_if_not_exists():
    """site.db 파일이 없으면 자동 생성"""
    db_path = os.path.join(app.root_path, "site.db")

    if not os.path.exists(db_path):
        print("⚠️  site.db가 없습니다. 새로 생성합니다...")
        with app.app_context():
            db.create_all()
        print("✅ DB 생성 완료!")

create_database_if_not_exists()