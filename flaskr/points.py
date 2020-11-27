import flaskr.pony_db as pony_db


def calculate_points():
    tournament = pony_db.get_tournament_by_status('koniec')
    if tournament is not None:
        bets = pony_db.get_bets_by_status('koniec')
        if bets is not None:
            for bet in bets:
                places = [bet.tournament_id.first_place,
                          bet.tournament_id.second_place,
                          bet.tournament_id.third_place]
                points = 0
                exact_bets = 0
                if bet.first_place in places:
                    points += 1
                if bet.second_place in places:
                    points += 1
                if bet.third_place in places:
                    points += 1
                if bet.first_place == places[0]:
                    points += 2
                    exact_bets += 1
                if bet.second_place == places[1]:
                    points += 2
                    exact_bets += 1
                if bet.third_place == places[2]:
                    points += 2
                    exact_bets += 1
                pony_db.update_user_stats(bet.user_id.id, points, exact_bets)
    pony_db.update_tournament_status(tournament.id, 'archiwum')
