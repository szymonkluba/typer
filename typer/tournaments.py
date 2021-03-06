from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from pony.orm import desc
from typer.auth import login_required
from typer.index import get_competitors
import typer.pony_db as pony_db


bp = Blueprint('tournaments', __name__, url_prefix='/tournaments')


@bp.route('/')
def tournaments():
    page = request.args.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    status = request.args.get('status')
    if status:
        tournaments = tournaments_status(status).sort_by(desc(pony_db.Tournaments.date_time))
    else:
        tournaments = pony_db.Tournaments.select().sort_by(desc(pony_db.Tournaments.date_time))
    pages = int(tournaments.count() / 5)
    tournaments = tournaments.page(page, 5)
    print(page, pages, status)
    return render_template("tournaments/tournaments.html",
                           tournaments=tournaments,
                           status=status,
                           page=page,
                           pages=pages)


def tournaments_status(status):
    return {
        "future": pony_db.Tournaments.select(lambda t: t.status == 'przyszłe'),
        "next": pony_db.Tournaments.select(lambda t: t.status == 'następne'),
        "end": pony_db.Tournaments.select(lambda t: t.status == 'koniec'),
        "archive": pony_db.Tournaments.select(lambda t: t.status == 'archiwum'),
        "cancelled": pony_db.Tournaments.select(lambda t: t.status == 'odwołane')
    }.get(status)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        place = request.form['place']
        typ = request.form['typ']
        status = request.form['status']
        date_time = request.form['date_time']
        error = None

        if not typ or not place or not status or not date_time:
            error = 'Nie podano wszystkich typów'

        if error is not None:
            flash(error)
        else:
            pony_db.create_tournament(place, typ, status, date_time)
            return redirect(url_for('tournaments.tournaments'))

    return render_template('tournaments/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    tournament = pony_db.Tournaments[id]
    if tournament is None:
        abort(404, f"Post id {id} does not exist.")
    if g.user.id != 1:
        abort(403)
    jumpers = get_competitors(tournament)
    if request.method == "POST":
        place = request.form['place']
        typ = request.form['type']
        status = request.form['status']
        date_time = request.form['date_time']
        first_place = request.form['first_place']
        second_place = request.form['second_place']
        third_place = request.form['third_place']
        error = None

        if error is not None:
            flash(error)
        else:
            pony_db.update_tournament(id, place, typ, status, date_time, first_place, second_place, third_place)
            return redirect(url_for('tournaments.tournaments'))

    return render_template('tournaments/update.html', tournament=tournament, jumpers=jumpers)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    tournament = pony_db.Tournaments[id]
    if tournament is None:
        abort(404, f"Post id {id} does not exist.")
    tournament.delete()
    return redirect(url_for('tournaments.tournaments'))
