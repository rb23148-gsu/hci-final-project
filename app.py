from flask import Flask, render_template, request, redirect, url_for, session, flash
from wtforms import Form, BooleanField, StringField, validators
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime
import re
import os
import pymysql

load_dotenv()
SQL_USER = os.environ.get('username')
SQL_PASSWORD = os.environ.get('sql_password')
SQL_HOST = os.environ.get('sql_host')
SQL_DB = 'grouploop_db'

app = Flask(__name__)
app.secret_key = os.urandom(24)

# PyMySQL documentation.https://pymysql.readthedocs.io/en/latest/
# This is a personal preference, allows to use written SQL commands using the cursor versus creating an object of SQLAlchemy.
# Can switch and learn the other if needed but for now going to use this. 
 
def connect_to_database():
    return pymysql.connect(host=SQL_HOST, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DB)

if __name__ == '__main__':
    app.run(debug=True)