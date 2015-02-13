from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin
from flask.ext.login import LoginManager

from aggregatorcomparor import admin_auth


app = Flask(__name__)
app.config.from_object('aggregatorcomparor.config')
app.config.from_pyfile('aggregatorcomparor.cfg', silent=True)
app.config.from_envvar('AGGREGATORCOMPAROR_CONFIG', silent=True)

db = SQLAlchemy(app)
login = LoginManager(app)
login.user_loader(admin_auth.get_administrator)
admin = Admin(app, index_view=admin_auth.AuthenticatedAdminIndexView())

