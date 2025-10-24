from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv 
import os 

load_dotenv() 

app = Flask(__name__)
CORS(app)

USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')
HOST = os.getenv('DB_HOST')
PORT = os.getenv('DB_PORT')
NAME = os.getenv('DB_NAME')
DATABASE_URI = f"mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}"


# 3. Use the retrieved URI for configuration
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'electiveapp24@gmail.com'
app.config['MAIL_PASSWORD'] = 'qpwhbopqdzlqihbt'

db = SQLAlchemy(app)
mail = Mail(app)

