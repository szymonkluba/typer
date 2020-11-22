from flask import (
    Blueprint, g, render_template,
)

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('ranking', __name__)


@bp.route('/ranking')
@login_required
def ranking():
    db = get_db()
    users = db.execute(
        'SELECT id, username, points, times_bet, times_exact FROM user'
        ' ORDER BY points DESC'
    ).fetchall()

    return render_template('ranking/ranking.html', users=users)
