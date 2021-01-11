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
        points.append((
            user,
            get_points_by_system(user, system),
            sum(p.times_exact for p in pony_db.Points if p.user == user),
            pony_db.Points.select(lambda p: p.user == user).count(),
            get_last_tournament_points(user, system, last_tournament),
            sum(p.times_exact for p in pony_db.Points if p.user == user and p.tournament == last_tournament),
            True if pony_db.Points.get(lambda p: p.user == user and p.tournament == last_tournament) else False
        ))
    return render_template('ranking/ranking.html',
                           points=sorted(points, key=itemgetter(1, 2), reverse=True),
                           system=system)


def get_points_by_system(user, system):
    return {
        "classic": sum(p.classic for p in pony_db.Points if p.user == user),
        "mg": sum(p.mg for p in pony_db.Points if p.user == user),
        "three_two": sum(p.three_two for p in pony_db.Points if p.user == user),
        "three_one": sum(p.three_one for p in pony_db.Points if p.user == user)
    }.get(system)


def get_last_tournament_points(user, system, last_tournament):
    return {
        "classic": sum(p.classic for p in pony_db.Points if p.user == user and p.tournament == last_tournament),
        "mg": sum(p.mg for p in pony_db.Points if p.user == user and p.tournament == last_tournament),
        "three_two": sum(p.three_two for p in pony_db.Points if p.user == user and p.tournament == last_tournament),
        "three_one": sum(p.three_one for p in pony_db.Points if p.user == user and p.tournament == last_tournament)
    }.get(system)
