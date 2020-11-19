from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('jumpers', __name__, url_prefix='/jumpers')


@bp.route('/')
def jumpers():
    db = get_db()
    jumpers = db.execute(
        'SELECT * FROM jumpers'
    ).fetchall()
    return render_template("jumpers/jumpers.html", jumpers=jumpers)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']

        error = None

        if not name:
            error = 'Nie podano nazwy/imienia'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO jumpers (name)'
                ' VALUES (?)',
                (name,)
            )
            db.commit()
            return redirect(url_for('jumpers.jumpers'))

    return render_template('jumpers/create.html')


def get_jumper(id):
    jumper = get_db().execute(
        'SELECT * FROM jumpers WHERE id = ?',
        (id,)
    ).fetchone()

    if jumper is None:
        abort(404, f"Post id {id} does not exist.")

    return jumper


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    jumper = get_jumper(id)

    if request.method == "POST":
        name = request.form['name']
        error = None

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE jumpers SET name = ? WHERE id = ?',
                (name, id)
            )
            db.commit()
            return redirect(url_for('jumpers.jumpers'))

    return render_template('jumpers/update.html', jumper=jumper)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_jumper(id)
    db = get_db()
    db.execute('DELETE FROM jumpers WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('jumpers.jumpers'))
