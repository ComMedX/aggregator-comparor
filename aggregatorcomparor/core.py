from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin
from flask.ext.login import LoginManager
from flask.ext.assets import (
    Bundle,
    Environment,
)


from aggregatorcomparor import admin_auth


app = Flask(__name__)
app.config.from_object('aggregatorcomparor.config')
app.config.from_pyfile('aggregatorcomparor.cfg', silent=True)
app.config.from_envvar('AGGREGATORCOMPAROR_CONFIG', silent=True)

db = SQLAlchemy(app)
login = LoginManager(app)
login.user_loader(admin_auth.get_administrator)
admin = Admin(app, index_view=admin_auth.AuthenticatedAdminIndexView())

assets = Environment(app)
assets.register("css_all", Bundle(
    "libs/bootstrap/dist/css/bootstrap.css",
    "libs/bootstrapxl.css",
    "css/style.css",
    'libs/font-awesome4/css/font-awesome.min.css',
    output="public/css/common.css"
))

assets.register("js_all", Bundle(
    "libs/jQuery/dist/jquery.js",
    "libs/jquery-migrate-1.2.1.js",
    "libs/bootstrap/dist/js/bootstrap.js",
    "libs/typeahead.bundle.js",
    "js/plugins.js",
    output="public/js/common.js"
))
