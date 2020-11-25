from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('typer', __name__)


@bp.route('/')
@login_required
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, p.first_place, p.second_place, p.third_place, created, user_id, username, tournament_id,'
        ' place, type, date_time, status FROM bets p'
        ' JOIN user u ON p.user_id = u.id'
        ' JOIN tournaments t ON p.tournament_id = t.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('typer/index.html',
                           posts=posts,
                           duplicate=check_for_duplicates())


@bp.route('/my_bets')
@login_required
def my_bets():
    db = get_db()
    if g.user['id'] is not None:
        posts = db.execute(
            'SELECT p.id, p.first_place, p.second_place, p.third_place, created, user_id, username, tournament_id,'
            ' place, type, date_time, status FROM bets p'
            ' JOIN user u ON p.user_id = u.id'
            ' JOIN tournaments t ON p.tournament_id = t.id'
            ' WHERE user_id = ?'
            ' ORDER BY created DESC',
            (g.user['id'],)
        ).fetchall()
        return render_template('typer/index.html',
                               posts=posts,
                               duplicate=check_for_duplicates())


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    db = get_db()
    tournament = db.execute(
        'SELECT id, place, type, date_time FROM tournaments'
        ' WHERE status = "następne"'
    ).fetchone()
    jumpers = get_jumpers()

    if request.method == 'POST':
        first_place = request.form['first_place']
        second_place = request.form['second_place']
        third_place = request.form['third_place']
        error = None

        if not first_place or not second_place or not third_place:
            error = 'Nie podano wszystkich typów'

        if error is not None:
            flash(error)
        else:
            db.execute(
                'INSERT INTO bets (first_place, second_place, third_place, user_id, tournament_id)'
                ' VALUES (?, ?, ?, ?, ?)',
                (first_place, second_place, third_place, g.user['id'], tournament['id'])
            )
            db.commit()
            return redirect(url_for('typer.index'))

    return render_template('typer/create.html',
                           tournament=tournament,
                           jumpers=jumpers)


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, p.first_place, p.second_place, p.third_place, created, user_id, username, tournament_id,'
        ' place, type, date_time FROM bets p'
        ' JOIN user u ON p.user_id = u.id'
        ' JOIN tournaments t ON p.tournament_id = t.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} does not exist.")

    if check_author and post['user_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)
    jumpers = get_jumpers(post)
    if request.method == "POST":
        first_place = request.form['first_place']
        second_place = request.form['second_place']
        third_place = request.form['third_place']
        error = None

        if not first_place or not second_place or not third_place:
            error = 'Nie podano wszystkich typów'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE bets SET first_place = ?, second_place = ?, third_place = ?'
                ' WHERE id = ?',
                (first_place, second_place, third_place, id)
            )
            db.commit()
            return redirect(url_for('typer.index'))

    return render_template('typer/update.html', post=post, jumpers=jumpers)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM bets WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('typer.index'))


def get_jumpers(selected_tournament=None):
    if selected_tournament is None:
        if check_type_of_tournament():
            jumpers = get_db().execute(
                'SELECT * FROM jumpers'
            ).fetchall()
        else:
            jumpers = get_db().execute(
                'SELECT * FROM countries'
            ).fetchall()
    else:
        if check_type_of_tournament(selected_tournament):
            jumpers = get_db().execute(
                'SELECT * FROM jumpers'
            ).fetchall()
        else:
            jumpers = get_db().execute(
                'SELECT * FROM countries'
            ).fetchall()
    return jumpers


def check_type_of_tournament(selected_tournament=None):
    if selected_tournament is None:
        type_of_tournament = get_db().execute(
            'SELECT type FROM tournaments WHERE status LIKE "następne"'
        ).fetchone()
        if type_of_tournament['type'] == 'indywidualne':
            return True
    else:
        type_of_tournament = selected_tournament
        if type_of_tournament['type'] == 'indywidualne':
            return True
    return False


def check_for_duplicates():
    if g.user['id'] is not None:
        current_tournament = get_db().execute(
            'SELECT id FROM tournaments WHERE status LIKE "następne"'
        ).fetchone()
        if current_tournament is not None:
            duplicate = get_db().execute(
                'SELECT * FROM bets WHERE user_id LIKE ? AND tournament_id LIKE ?',
                (g.user['id'], current_tournament['id'])
            ).fetchone()
            if duplicate is not None:
                return True
        else:
            return True
    return False
