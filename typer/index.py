from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from typer.auth import login_required
import typer.pony_db as pony_db

bp = Blueprint('index', __name__)


@bp.route('/')
@login_required
def index():
    page = request.args.get('page')
    status = request.args.get('bets')
    if not page:
        page = 1
    else:
        page = int(page)
    if status and status == 'my':
        bets = pony_db.get_bets(g.user.id)
    else:
        bets = pony_db.get_bets()
    pages = int(bets.count() / 10)
    bets = bets.page(page)
    return render_template('typer/index.html',
                           bets=bets,
                           page=page,
                           pages=pages,
                           status=status,
                           duplicate=check_for_duplicates(),
                           current_tournament=pony_db.Tournaments.get(lambda t: t.status == 'następne'))


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create(tournament=None):
    tournament_id = request.args.get("tournament_id")
    if not tournament_id:
        tournament = pony_db.Tournaments.get(lambda t: t.status == 'następne')
    else:
        tournament = pony_db.Tournaments.get(lambda t: t.id == int(tournament_id))
    participants = False
    jumpers = None
    error = None
    if tournament.participants:
        participants = tournament.participants
    else:
        jumpers = get_competitors()

    if check_for_duplicates(tournament):
        error = "Już typowałeś te zawody"
        flash(error)
        return redirect(url_for("index.index"))

    if request.method == 'POST':
        first_place = request.form['first_place']
        second_place = request.form['second_place']
        third_place = request.form['third_place']
        error = None

        if not first_place or not second_place or not third_place:
            error = 'Nie podano wszystkich typów'

        if (not pony_db.check_valid_bet(first_place)
                or not pony_db.check_valid_bet(second_place)
                or not pony_db.check_valid_bet(first_place)):
            error = "Nie ma takiego typowania! Proszę wybrać z listy;)"

        if error is not None:
            flash(error)
        else:
            pony_db.create_bet(first_place,
                               second_place,
                               third_place,
                               g.user.id,
                               tournament)
            return redirect(url_for('index.index'))

    return render_template('typer/create.html',
                           tournament=tournament,
                           jumpers=jumpers,
                           participants=participants)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    bet = pony_db.Bets[id]
    if bet is None:
        abort(404, f"Post id {id} does not exist.")
    if bet.user_id.id != g.user.id:
        abort(403)
    tournament = bet.tournament_id
    participants = False
    competitors = None
    if tournament.participants:
        participants = tournament.participants
    else:
        competitors = get_competitors(tournament)
    if request.method == "POST":
        first_place = request.form['first_place']
        second_place = request.form['second_place']
        third_place = request.form['third_place']
        error = None

        if (not pony_db.check_valid_bet(first_place)
                or not pony_db.check_valid_bet(second_place)
                or not pony_db.check_valid_bet(first_place)):
            error = "Nie ma takiego typowania! Co kurwa osiemnastka jest? Proszę wybrać z listy;)"

        if not first_place or not second_place or not third_place:
            error = 'Nie podano wszystkich typów'

        if error is not None:
            flash(error)
        else:
            pony_db.update_bet(first_place, second_place, third_place, id)
            return redirect(url_for('index.index'))

    return render_template('typer/update.html', bet=bet, jumpers=competitors, participants=participants)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    post = pony_db.Bets[id]
    if post is None:
        abort(404, f"Post id {id} does not exist.")
    pony_db.Bets[id].delete()
    return redirect(url_for('index.index'))


def get_competitors(selected_tournament=None):
    if selected_tournament is None:
        if check_type_of_tournament():
            competitors = pony_db.Jumpers.select()
        else:
            competitors = pony_db.Countries.select()
    else:
        if check_type_of_tournament(selected_tournament):
            competitors = pony_db.Jumpers.select()
        else:
            competitors = pony_db.Countries.select()
    return competitors


def check_type_of_tournament(selected_tournament=None):
    if selected_tournament is None:
        type_of_tournament = pony_db.Tournaments.get(lambda t: t.status == 'następne')
        if 'indywidualne' == type_of_tournament.type:
            return True
    else:
        type_of_tournament = selected_tournament
        if 'indywidualne' in type_of_tournament.type:
            return True
    return False


def check_for_duplicates(tournament=None):
    if g.user.id is not None:
        if tournament:
            current_tournament = tournament
        else:
            current_tournament = pony_db.Tournaments.get(lambda t: t.status == 'następne')
        if current_tournament is not None:
            return pony_db.duplicate_bet_exists(g.user.id, current_tournament)
        else:
            return True
    return False
