from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('ranking', __name__)

@bp.route('/ranking')
@login_required
def ranking():
    db = get_db()
    users = db.execute(
        'SELECT id, username, points, times_bet, times_exact FROM user'
    ).fetchall()

    return render_template('ranking/ranking.html', users=users)