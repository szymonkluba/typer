from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('typer', __name__)


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, p.first_place, p.second_place, p.third_place, created, user_id, username, tournament_id,'
        ' place, type, date_time FROM bets p JOIN user u ON p.user_id = u.id JOIN tournaments t ON p.tournament_id = t.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('typer/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        first_place = request.form['first_place']
        second_place = request.form['second_place']
        third_place = request.form['third_place']
        error = None

        if not first_place or second_place or third_place:
            error = 'Nie podano wszystkich typów'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO bets (first_place, second_place, third_place, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('typer.index'))

    return render_template('typer/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} does not exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == "POST":
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = "Title is rquired."
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                " WHERE id = ?",
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('typer.index'))

    return render_template('typer/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('typer.index'))
