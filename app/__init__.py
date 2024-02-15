from urllib.parse import quote

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = '#$#$#$#$#$#$'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/hotel?charset=utf8mb4" % quote("Admin@123") #mysql database
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config['CART_KEY'] = 'cart'
app.config['UPLOAD_FILE'] = 'hotel/app/static/img'

db = SQLAlchemy(app=app)
login = LoginManager(app=app)