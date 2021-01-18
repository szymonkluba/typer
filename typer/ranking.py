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
        recent_bet = pony_db.Points.get(lambda p: p.user == user and p.tournament == last_tournament)
        points.append({
            "user": user,
            "points": get_points_by_system(user, system),
            "exact": sum(p.times_exact for p in pony_db.Points if p.user == user),
            "times_bet": bets.count(),
            "points_recent": get_last_tournament_points(user, system, last_tournament),
            "exact_recent": sum(p.times_exact for p in pony_db.Points if p.user == user and p.tournament == last_tournament),
            "bet_recent": True if recent_bet else False,
            "bets": bets
        })
    return render_template('ranking/ranking.html',
                           points=sorted(points, key=itemgetter("points", "exact"), reverse=True),
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
