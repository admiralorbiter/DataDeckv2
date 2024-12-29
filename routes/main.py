from flask import render_template
from .base import create_blueprint

bp = create_blueprint('main')

@bp.route('/')
def index():
    return render_template('index.html') 