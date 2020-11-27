from flask import (
    Blueprint, g, render_template,
)

from flaskr.auth import login_required
import flaskr.pony_db as pony_db

bp = Blueprint('ranking', __name__)


@bp.route('/ranking')
@login_required
def ranking():
    users = pony_db.get_users_ranking()

    return render_template('ranking/ranking.html', users=users)
