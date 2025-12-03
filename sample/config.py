import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    GOOGLE_CLIENT_ID = "861514102522-c8vppikutcunjkj8qshqp2f5c76n926s.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET = "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"
    GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'profile_pics')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
