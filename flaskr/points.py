import flaskr.pony_db as pony_db


def calculate_points():
    tournament = pony_db.get_tournament_by_status('koniec')
    if tournament:
        if tournament.type == 'drużynowe':
            results = pony_db.get_fives_for_tournament(tournament.id)
        else:
            results = pony_db.get_tens_for_tournament(tournament.id)
        bets = pony_db.get_bets_by_status('koniec')
        if bets is not None:
            for bet in bets:
                if bet.tournament_id.type == 'drużynowe':
                    places = [bet.tournament_id.first_place.country_id.id,
                              bet.tournament_id.second_place.country_id.id,
                              bet.tournament_id.third_place.country_id.id]
                    first_place = bet.first_place.country_id.id
                    second_place = bet.second_place.country_id.id
                    third_place = bet.third_place.country_id.id
                else:
                    places = [bet.tournament_id.first_place.jumper_id.id,
                              bet.tournament_id.second_place.jumper_id.id,
                              bet.tournament_id.third_place.jumper_id.id]
                    first_place = bet.first_place.jumper_id.id
                    second_place = bet.second_place.jumper_id.id
                    third_place = bet.third_place.jumper_id.id
                points = 0
                exact_bets = 0
                if first_place in places:
                    points += 1
                if second_place in places:
                    points += 1
                if third_place in places:
                    points += 1
                if first_place == places[0]:
                    points += 2
                    exact_bets += 1
                if second_place == places[1]:
                    points += 1
                    exact_bets += 1
                if third_place == places[2]:
                    points += 1
                    exact_bets += 1
                try:
                    if first_place in results[1]:
                        points -= 1
                    elif first_place in results[2]:
                        points -= 2
                except IndexError:
                    pass
                try:
                    if second_place in results[1]:
                        points -= 1
                    elif second_place in results[2]:
                        points -= 2
                except IndexError:
                    pass
                try:
                    if third_place in results[1]:
                        points -= 1
                    elif third_place in results[2]:
                        points -= 2
                except IndexError:
                    pass
                pony_db.update_user_stats(bet.user_id.id, points, exact_bets)
    pony_db.update_tournament_status(tournament.id, 'archiwum')
