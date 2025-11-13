from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS

from application import app

app.secret_key = 'prodigy_carwash_app'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/db_prodigy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

csrf = CSRFProtect()
csrf.init_app(app)