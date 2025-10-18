from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv 
import os 

load_dotenv() 

app = Flask(__name__)

USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')
HOST = os.getenv('DB_HOST')
PORT = os.getenv('DB_PORT')
NAME = os.getenv('DB_NAME')
DATABASE_URI = f"mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}"


# 3. Use the retrieved URI for configuration
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
