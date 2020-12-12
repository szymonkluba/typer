from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from typer.auth import login_required
from itertools import groupby
import typer.pony_db as pony_db

bp = Blueprint('jumpers', __name__, url_prefix='/jumpers')


@bp.route('/')
def jumpers():
    jumpers = pony_db.get_jumpers()
    jumpers = [list(g) for k, g in groupby(sorted(jumpers, key=lambda x: x.name), lambda x: x.name[0])]
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
            pony_db.create_jumper(name)
            return redirect(url_for('jumpers.jumpers'))

    return render_template('jumpers/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    jumper = pony_db.get_jumper_by_id(id)
    if jumper is None:
        abort(404, f"Post id {id} does not exist.")
    if g.user.id != 1:
        abort(403)
    if request.method == "POST":
        name = request.form['name']
        error = None

        if error is not None:
            flash(error)
        else:
            pony_db.update_jumper(id, name)
            return redirect(url_for('jumpers.jumpers'))

    return render_template('jumpers/update.html', jumper=jumper)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    jumper = pony_db.get_jumper_by_id(id)
    if jumper is None:
        abort(404, f"Post id {id} does not exist.")
    pony_db.delete_jumper(id)
    return redirect(url_for('jumpers.jumpers'))