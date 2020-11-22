from flaskr.db import get_db


def calculate_points():
    points = 0
    exact_bets = 0
    tournaments = get_tournaments()
    if tournaments is not None:
        for tournament in tournaments:
            bets = get_bets(tournament)
            places = [tournament['first_place'], tournament['second_place'], tournament['third_place']]
            if bets is not None:
                for bet in bets:
                    if bet['first_place'] in places:
                        points += 1
                    if bet['second_place'] in places:
                        points += 1
                    if bet['third_place'] in places:
                        points += 1
                    if bet['first_place'] == places[0]:
                        points += 2
                        exact_bets += 1
                    if bet['second_place'] == places[1]:
                        points += 2
                        exact_bets += 1
                    if bet['third_place'] == places[2]:
                        points += 2
                        exact_bets += 1
                    db = get_db()
                    db.execute(
                        'UPDATE user SET points = points + ?, times_exact = times_exact + ?, times_bet = times_bet + 1'
                        ' WHERE id = ?',
                        (points, exact_bets, bet['user_id'])
                    )
                    db.commit()
            db = get_db()
            db.execute(
                'UPDATE tournaments SET status = "archiwum" WHERE id = ?',
                (tournament['id'],)
            )
            db.commit()


def get_tournaments():
    tournaments = get_db().execute(
        'SELECT id, first_place, second_place, third_place'
        ' FROM tournaments WHERE status LIKE "koniec"'
    ).fetchall()
    return tournaments


def get_bets(tournament):
    if tournament is not None:
        bets = get_db().execute(
            'SELECT user_id, first_place, second_place, third_place'
            ' FROM bets WHERE tournament_id = ?',
            (tournament['id'],)
        ).fetchall()
    return bets
