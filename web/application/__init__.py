from flask import Flask

app = Flask(__name__)

from application import api
from application import views

app.register_blueprint(api.api)
# app.register_blueprint(views.views)

