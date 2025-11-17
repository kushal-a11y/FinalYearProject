from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

USERNAME=os.getenv('DB_USERNAME')
PASSWORD=os.getenv('DB_PASSWORD')
HOST=os.getenv('DB_HOST')
PORT=os.getenv('DB_PORT')
NAME=os.getenv('DB_NAME')

app.config["SQLALCHEMY_DATABASE_URI"]=f"mysql+mysqlconnector://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False

db = SQLAlchemy(app)
