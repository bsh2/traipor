from flask import Blueprint

training = Blueprint('training', __name__)

from . import views
