from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('tournaments', __name__, url_prefix='/tournaments')


@bp.route('/')
def tournaments():
    db = get_db()
    tournaments = db.execute(
        'SELECT id, place, type, date_time, first_place, second_place, third_place'
        ' FROM tournaments ORDER BY date_time DESC'
    ).fetchall()
    return render_template("tournaments/tournaments.html", tournaments=tournaments)


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
            db = get_db()
            db.execute(
                'INSERT INTO tournaments (place, type, status, date_time, first_place, second_place, third_place)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                (place, typ, status, date_time, 'TBA', 'TBA', 'TBA')
            )
            db.commit()
            return redirect(url_for('tournaments.tournaments'))

    return render_template('tournaments/create.html')


def get_tournament(id):
    tournament = get_db().execute(
        'SELECT * FROM tournaments WHERE id = ?',
        (id,)
    ).fetchone()

    if tournament is None:
        abort(404, f"Post id {id} does not exist.")

    return tournament


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    tournament = get_tournament(id)

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
            db = get_db()
            db.execute(
                'UPDATE tournaments SET place = ?, type = ?, status = ?, date_time = ?,'
                "first_place = ?, second_place = ?, third_place = ? WHERE id = ?",
                (place, typ, status, date_time, first_place, second_place, third_place, id)
            )
            db.commit()
            return redirect(url_for('tournaments.tournaments'))

    return render_template('tournaments/update.html', tournament=tournament)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_tournament(id)
    db = get_db()
    db.execute('DELETE FROM tournaments WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('tournaments.tournaments'))
