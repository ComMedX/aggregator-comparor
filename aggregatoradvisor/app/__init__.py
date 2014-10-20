from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__)



import views
import models
