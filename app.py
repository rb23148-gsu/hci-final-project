from flask import Flask, render_template, request, redirect, url_for, session, flash
from wtforms import Form, BooleanField, StringField, validators
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import func
import re
from decimal import Decimal
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'GroupLoop'




if __name__ == '__main__':
    app.run(debug=True)