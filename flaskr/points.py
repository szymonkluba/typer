import flaskr.pony_db as pony_db


def calculate_points():
    tournament = pony_db.get_tournament_by_status('koniec')
    if tournament:
        if tournament.type == 'drużynowe':
            first_part = pony_db.get_first_five(tournament.id)
            second_part = pony_db.get_second_five(tournament.id)
        else:
            first_part = pony_db.get_first_ten(tournament.id)
            second_part = pony_db.get_second_ten(tournament.id)
        print(first_part)
        print(second_part)
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
                if check_fives_or_tens(first_place, first_part):
                    points -= 1
                    print(f'{pony_db.Jumpers[first_place].name}')
                    print('Nie ma w pierwszej części_________________________')
                    if check_fives_or_tens(first_place, second_part):
                        points -= 1
                        print(f'{pony_db.Jumpers[first_place].name}')
                        print('Nie ma w drugiej części--------------------------')
                if check_fives_or_tens(second_place, first_part):
                    points -= 1
                    print(f'{pony_db.Jumpers[second_place].name}')
                    print('Nie ma w pierwszej części_________________________')
                    if check_fives_or_tens(second_place, second_part):
                        points -= 1
                        print(f'{pony_db.Jumpers[second_place].name}')
                        print('Nie ma w drugiej części--------------------------')
                if check_fives_or_tens(third_place, first_part):
                    points -= 1
                    print(f'{pony_db.Jumpers[third_place].name}')
                    print('Nie ma w pierwszej części_________________________')
                    if check_fives_or_tens(third_place, second_part):
                        points -= 1
                        print(f'{pony_db.Jumpers[third_place].name}')
                        print('Nie ma w drugiej części--------------------------')
                pony_db.update_user_stats(bet.user_id.id, points, exact_bets)
    pony_db.update_tournament_status(tournament.id, 'archiwum')


def check_fives_or_tens(place, list_of_places):
    for i in list_of_places:
        if place == i:
            return False
    return True
