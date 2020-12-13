import typer.pony_db as pony_db
from pony.orm import db_session


@db_session
def calculate_points(tournaments=None):
    if not tournaments:
        tournaments = pony_db.Tournaments.select(lambda t: t.status == "archiwum")
    if tournaments:
        for tournament in tournaments:
            if tournament.bets:
                for bet in tournament.bets:
                    if not pony_db.points_exists(bet.user_id, tournament):
                        pony_db.Points(user=bet.user_id, tournament=tournament)
                        if tournament.type == "drużynowe":
                            if (bet.first_place.country_id == tournament.second_place.country_id or
                                    bet.first_place.country_id == tournament.third_place.country_id):
                                pony_db.update_points(bet.user_id, tournament,
                                                      classic=1, mg=1, three_two=1, three_one=1)
                            if (bet.second_place.country_id == tournament.first_place.country_id or
                                    bet.second_place.country_id == tournament.third_place.country_id):
                                pony_db.update_points(bet.user_id, tournament,
                                                      classic=1, mg=1, three_two=1, three_one=1)
                            if (bet.third_place.country_id == tournament.first_place.country_id or
                                    bet.third_place.country_id == tournament.second_place.country_id):
                                pony_db.update_points(bet.user_id, tournament,
                                                      classic=1, mg=1, three_two=1, three_one=1)
                            if bet.first_place.country_id == tournament.first_place.country_id:
                                pony_db.update_points(bet.user_id, tournament,
                                                      classic=3, mg=3, three_two=3, three_one=3, exact=1)
                            if bet.second_place.country_id == tournament.second_place.country_id:
                                pony_db.update_points(bet.user_id, tournament,
                                                      classic=3, mg=2, three_two=2, three_one=1, exact=1)
                            if bet.third_place.country_id == tournament.third_place.country_id:
                                pony_db.update_points(bet.user_id, tournament,
                                                      classic=3, mg=2, three_two=2, three_one=1, exact=1)
                            if bet.first_place.country_id not in tournament.first_five.country_id:
                                pony_db.update_points(bet.user_id, tournament, mg=-1)
                                if bet.first_place.country_id not in tournament.second_five.country_id:
                                    pony_db.update_points(bet.user_id, tournament, mg=-1)
                            if bet.second_place.country_id not in tournament.first_five.country_id:
                                pony_db.update_points(bet.user_id, tournament, mg=-1)
                                if bet.second_place.country_id not in tournament.second_five.country_id:
                                    pony_db.update_points(bet.user_id, tournament, mg=-1)
                            if bet.third_place.country_id not in tournament.first_five.country_id:
                                pony_db.update_points(bet.user_id, tournament, mg=-1)
                                if bet.third_place.country_id not in tournament.second_five.country_id:
                                    pony_db.update_points(bet.user_id, tournament, mg=-1)
                        else:
                            if (bet.first_place.jumper_id == tournament.second_place.jumper_id or
                                    bet.first_place.jumper_id == tournament.third_place.jumper_id):
                                pony_db.update_points(bet.user_id, tournament,
                                                      classic=1, mg=1, three_two=1, three_one=1)
                            if (bet.second_place.jumper_id == tournament.first_place.jumper_id or
                                    bet.second_place.jumper_id == tournament.third_place.jumper_id):
                                pony_db.update_points(bet.user_id, tournament,
                                                      classic=1, mg=1, three_two=1, three_one=1)
                            if (bet.third_place.jumper_id == tournament.first_place.jumper_id or
                                    bet.third_place.jumper_id == tournament.second_place.jumper_id):
                                pony_db.update_points(bet.user_id, tournament,
                                                      classic=1, mg=1, three_two=1, three_one=1)
                            if bet.first_place.jumper_id == tournament.first_place.jumper_id:
                                pony_db.update_points(bet.user_id, tournament,
                                                      classic=3, mg=3, three_two=3, three_one=3, exact=1)
                            if bet.second_place.jumper_id == tournament.second_place.jumper_id:
                                pony_db.update_points(bet.user_id, tournament,
                                                      classic=3, mg=2, three_two=2, three_one=1, exact=1)
                            if bet.third_place.jumper_id == tournament.third_place.jumper_id:
                                pony_db.update_points(bet.user_id, tournament,
                                                      classic=3, mg=2, three_two=2, three_one=1, exact=1)
                            if bet.first_place.jumper_id not in tournament.first_ten.jumper_id:
                                pony_db.update_points(bet.user_id, tournament, mg=-1)
                                if bet.first_place.jumper_id not in tournament.second_ten.jumper_id:
                                    pony_db.update_points(bet.user_id, tournament, mg=-1)
                            if bet.second_place.jumper_id not in tournament.first_ten.jumper_id:
                                pony_db.update_points(bet.user_id, tournament, mg=-1)
                                if bet.second_place.jumper_id not in tournament.second_ten.jumper_id:
                                    pony_db.update_points(bet.user_id, tournament, mg=-1)
                            if bet.third_place.jumper_id not in tournament.first_ten.jumper_id:
                                pony_db.update_points(bet.user_id, tournament, mg=-1)
                                if bet.third_place.jumper_id not in tournament.second_ten.jumper_id:
                                    pony_db.update_points(bet.user_id, tournament, mg=-1)
                            print(f"LOG: Points for {tournament.place} - {tournament.type} for user: "
                                  f"{bet.user_id.username} have been calculated", flush=True)
                    else:
                        print(f"LOG: Points for {tournament.place} - {tournament.type} are already calculated.",
                              flush=True)
            else:
                print(f"LOG: No bets for {tournament.place} - {tournament.type}.", flush=True)
    else:
        print("LOG: No tournaments for points calculation.", flush=True)
