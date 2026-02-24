from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

# Load DB credentials from .env
USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')
HOST = os.getenv('DB_HOST')
PORT = os.getenv('DB_PORT')
NAME = os.getenv('DB_NAME')

MAIL_USERNAME='matrimonialmatchmaker996@gmail.com'
MAIL_PASSWORD='hcavuoutjejscvuq'

app.config['SQLALCHEMY_DATABASE_URI'] = \
    'mysql+pymysql://matriuser:1234@localhost/matrimony_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration FIRST, before importing routes
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD')
)

db = SQLAlchemy(app)
mail = Mail(app)

