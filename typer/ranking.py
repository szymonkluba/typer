from flask import (
    Blueprint, g, render_template,
)

from typer.auth import login_required
import typer.pony_db as pony_db
from pony.orm import count, sum, desc
from operator import itemgetter

bp = Blueprint('ranking', __name__)


@bp.route('/ranking/<system>')
@login_required
def ranking(system):
    points = []
    users = pony_db.User.select()
    last_tournament = pony_db.Tournaments.select(lambda t: t.status == "archiwum").sort_by(desc(pony_db.Tournaments.date_time)).first()
    for user in users:
        bets = pony_db.Points.select(lambda p: p.user == user)
        points.append({
            "user": user,
            "points": get_points_by_system(user, system),
            "exact": sum(p.times_exact for p in pony_db.Points if p.user == user),
            "times_bet": bets.count(),
            "bets": bets
        })
    return render_template('ranking/ranking.html',
                           points=sorted(points, key=itemgetter("points", "exact"), reverse=True),
                           last_tournament=last_tournament,
                           system=system)


def get_points_by_system(user, system):
    return {
        "classic": sum(p.classic for p in pony_db.Points if p.user == user),
        "mg": sum(p.mg for p in pony_db.Points if p.user == user),
        "three_two": sum(p.three_two for p in pony_db.Points if p.user == user),
        "three_one": sum(p.three_one for p in pony_db.Points if p.user == user)
    }.get(system)

