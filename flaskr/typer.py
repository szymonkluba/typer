from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
import flaskr.pony_db as pony_db

bp = Blueprint('typer', __name__)


@bp.route('/')
@login_required
def index():
    return render_template('typer/index.html',
                           bets=pony_db.get_bets(),
                           duplicate=check_for_duplicates(),
                           current_tournament=pony_db.get_tournament_by_status('następne'))


@bp.route('/my_bets')
@login_required
def my_bets():
    if g.user.id is not None:
        posts = pony_db.get_bets(g.user.id)
        return render_template('typer/index.html',
                               bets=posts,
                               duplicate=check_for_duplicates(),
                               current_tournament=pony_db.get_tournament_by_status('następne'))


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    tournament = pony_db.get_tournament_by_status('następne')
    participants = False
    if tournament.participants:
        participants = tournament.participants
    else:
        jumpers = get_competitors()

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
            pony_db.create_bet(first_place,
                               second_place,
                               third_place,
                               g.user.id,
                               tournament)
            return redirect(url_for('typer.index'))

    return render_template('typer/create.html',
                           tournament=tournament,
                           jumpers=jumpers,
                           participants=participants)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    bet = pony_db.get_bet(id)
    if bet is None:
        abort(404, f"Post id {id} does not exist.")
    tournament = pony_db.get_tournament(bet.tournament_id.id)
    participants = False
    if tournament.participants:
        participants = tournament.participants
    else:
        competitors = get_competitors(tournament)
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
            pony_db.update_bet(first_place, second_place, third_place, id)
            return redirect(url_for('typer.index'))

    return render_template('typer/update.html', bet=bet, jumpers=competitors, participants=participants)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    post = pony_db.get_bet(id)
    if post is None:
        abort(404, f"Post id {id} does not exist.")
    pony_db.delete_bet(id)
    return redirect(url_for('typer.index'))


def get_competitors(selected_tournament=None):
    if selected_tournament is None:
        if check_type_of_tournament():
            competitors = pony_db.get_jumpers()
        else:
            competitors = pony_db.get_countries()
    else:
        if check_type_of_tournament(selected_tournament):
            competitors = pony_db.get_jumpers()
        else:
            competitors = pony_db.get_countries()
    return competitors


def check_type_of_tournament(selected_tournament=None):
    if selected_tournament is None:
        type_of_tournament = pony_db.get_tournament_by_status('następne')
        if 'indywidualne' == type_of_tournament.type:
            return True
    else:
        type_of_tournament = selected_tournament
        if 'indywidualne' in type_of_tournament.type:
            return True
    return False


def check_for_duplicates():
    if g.user.id is not None:
        current_tournament = pony_db.get_tournament_by_status('następne')
        if current_tournament is not None:
            return pony_db.duplicate_bet_exists(g.user.id, current_tournament)
        else:
            return True
    return False
