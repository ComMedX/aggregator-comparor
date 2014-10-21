from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin
from flask.ext.login import LoginManager

from admin_auth import AuthenticatedAdminIndexView

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
admin = Admin(app, index_view=AuthenticatedAdminIndexView())
login = LoginManager(app)

import models
import admin_ui
import views

