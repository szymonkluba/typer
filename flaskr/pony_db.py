from pony.orm import *
from datetime import datetime

db = Database()
db.bind(provider='sqlite',
        filename='../instance/flaskr.sqlite',
        create_db=True)


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    username = Required(str, unique=True)
    password = Required(str)
    times_bet = Optional(int, default=0)
    times_exact = Optional(int, default=0)
    points = Optional(int, default=0)
    bets = Set("Bets")


class Jumpers(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    first_place = Set('FirstPlaces')
    second_place = Set('SecondPlaces')
    third_place = Set('ThirdPlaces')
    first_ten = Set('FirstTen')
    second_ten = Set('SecondTen')
    third_ten = Set('ThirdTen')


class Countries(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    first_place = Set('FirstPlaces')
    second_place = Set('SecondPlaces')
    third_place = Set('ThirdPlaces')
    first_five = Set('FirstFive')
    second_five = Set('SecondFive')
    third_five = Set('ThirdFive')


class FirstPlaces(db.Entity):
    tournament_id = Optional('Tournaments')
    bet_id = Optional('Bets')
    jumper_id = Optional('Jumpers')
    country_id = Optional('Countries')


class SecondPlaces(db.Entity):
    tournament_id = Optional('Tournaments')
    bet_id = Optional('Bets')
    jumper_id = Optional('Jumpers')
    country_id = Optional('Countries')


class ThirdPlaces(db.Entity):
    tournament_id = Optional('Tournaments')
    bet_id = Optional('Bets')
    jumper_id = Optional('Jumpers')
    country_id = Optional('Countries')


class Tournaments(db.Entity):
    id = PrimaryKey(int, auto=True)
    place = Required(str)
    type = Required(str)
    date_time = Required(datetime)
    first_place = Optional(FirstPlaces)
    second_place = Optional(SecondPlaces)
    third_place = Optional(ThirdPlaces)
    first_ten = Set('FirstTen')
    second_ten = Set('SecondTen')
    third_ten = Set('ThirdTen')
    first_five = Set('FirstFive')
    second_five = Set('SecondFive')
    third_five = Set('ThirdFive')
    status = Required(str)
    fis_id = Required(int)
    bets = Set('Bets')


class Bets(db.Entity):
    id = PrimaryKey(int, auto=True)
    user_id = Required(User)
    created = Required(datetime, sql_default='CURRENT_TIMESTAMP')
    tournament_id = Required(Tournaments)
    first_place = Optional('FirstPlaces')
    second_place = Optional('SecondPlaces')
    third_place = Optional('ThirdPlaces')


class FirstTen(db.Entity):
    tournament_id = Required(Tournaments)
    jumper_id = Required(Jumpers)


class SecondTen(db.Entity):
    tournament_id = Required(Tournaments)
    jumper_id = Required(Jumpers)


class ThirdTen(db.Entity):
    tournament_id = Required(Tournaments)
    jumper_id = Required(Jumpers)


class FirstFive(db.Entity):
    tournament_id = Required(Tournaments)
    country_id = Required(Countries)


class SecondFive(db.Entity):
    tournament_id = Required(Tournaments)
    country_id = Required(Countries)


class ThirdFive(db.Entity):
    tournament_id = Required(Tournaments)
    country_id = Required(Countries)


db.generate_mapping(create_tables=True)


def get_bets(id=None):
    if id is None:
        bets = Bets.select().sort_by(desc(Bets.created))
    else:
        bets = Bets.select(lambda b: b.user_id.id == id).sort_by(desc(Bets.created))
    return bets


def get_bets_by_status(status):
    bets = Bets.select(lambda b: b.tournament_id.status == status)
    return bets


def get_bet(id):
    bet = Bets.get(lambda b: b.id == id)
    return bet


def delete_bet(id):
    Bets[id].delete()
    commit()


def create_bet(first_place, second_place, third_place, user_id, tournament_id):
    bet = Bets(user_id=user_id, tournament_id=tournament_id.id)
    bet.flush()
    if tournament_id.type == "drużynowe":
        first_place = get_country_by_name(first_place)
        second_place = get_country_by_name(second_place)
        third_place = get_country_by_name(third_place)
        bet_places_team(first_place, second_place, third_place, bet.id, update=False)
    elif tournament_id.type == "indywidualne":
        first_place = get_jumper_by_name(first_place)
        second_place = get_jumper_by_name(second_place)
        third_place = get_jumper_by_name(third_place)
        bet_places_individual(first_place, second_place, third_place, bet.id, update=False)
    commit()


def update_bet(first_place, second_place, third_place, id):
    if Bets[id].tournament_id.type == 'drużynowe':
        first_place = get_country_by_name(first_place)
        second_place = get_country_by_name(second_place)
        third_place = get_country_by_name(third_place)
        bet_places_team(first_place, second_place, third_place, id)
    else:
        first_place = get_jumper_by_name(first_place)
        second_place = get_jumper_by_name(second_place)
        third_place = get_jumper_by_name(third_place)
        bet_places_individual(first_place, second_place, third_place, id)
    commit()


def duplicate_bet_exists(user_id, tournament_id):
    return exists(b for b in Bets if b.user_id.id == user_id and b.tournament_id.id == tournament_id.id)


def get_tournaments():
    tournaments = Tournaments.select().sort_by(desc(Tournaments.date_time))
    return tournaments


def get_tournament(id):
    tournament = Tournaments.get(lambda t: t.id == id)
    return tournament


def get_tournament_by_status(status):
    current_tournament = Tournaments.get(lambda t: t.status == status)
    return current_tournament


def select_tournaments_for_update():
    tournaments = Tournaments.select(lambda t: t.status == 'następne' or t.status == 'przyszłe')
    return tournaments


def get_last_fis_id():
    fis_id = select(t.fis_id for t in Tournaments).max()
    if fis_id:
        return fis_id
    else:
        return 5786


def open_next_tournament():
    tournament = Tournaments.select(lambda t: t.status == "przyszłe").sort_by(Tournaments.date_time).first()
    tournament.set(status="następne")
    commit()


def create_tournament(place, type, status, date_time, fis_id):
    tournament = Tournaments(place=place,
                             type=type,
                             status=status,
                             date_time=date_time,
                             fis_id=fis_id)
    tournament.flush()
    country_tba = get_countries_tba()
    jumper_tba = get_jumpers_tba()
    FirstPlaces(tournament_id=tournament.id, jumper_id=jumper_tba.id, country_id=country_tba.id)
    SecondPlaces(tournament_id=tournament.id, jumper_id=jumper_tba.id, country_id=country_tba.id)
    ThirdPlaces(tournament_id=tournament.id, jumper_id=jumper_tba.id, country_id=country_tba.id)
    commit()


def update_tournament(id, place, type, status, date_time, first_place, second_place, third_place):
    Tournaments[id].set(place=place,
                        type=type,
                        status=status,
                        date_time=date_time)
    update_tournament_places(type, FirstPlaces, first_place, id) if first_place != 'TBA' else None
    update_tournament_places(type, SecondPlaces, second_place, id) if second_place != 'TBA' else None
    update_tournament_places(type, ThirdPlaces, third_place, id) if third_place != 'TBA' else None
    commit()


def update_tournament_podium(id, type, first_place, second_place, third_place):
    update_tournament_places(type, FirstPlaces, first_place, id)
    update_tournament_places(type, SecondPlaces, second_place, id)
    update_tournament_places(type, ThirdPlaces, third_place, id)
    commit()


def update_tournament_places(type, table, place, id):
    row = table.get(lambda t: t.tournament_id.id == id)
    if type == 'drużynowe':
        row.set(country_id=get_country_by_name(place).id)
    elif type == "indywidualne":
        row.set(jumper_id=get_jumper_by_name(place).id)


def update_tournament_status(id, status):
    Tournaments[id].set(status=status)
    commit()


def update_tournament_date_time(id, date_time):
    Tournaments[id].set(date_time=date_time)
    commit()


def delete_tournament(id):
    Tournaments[id].delete()
    commit()


def get_users():
    users = User.select()
    return users


def get_user(id=None, username=None, password=None):
    if id is not None:
        user = User.get(lambda u: u.id == id)
        return user
    if username is not None:
        user = User.get(lambda u: u.username == username)
        return user
    if password is not None:
        user = User.get(lambda u: u.password == password)
        return user


def get_users_ranking():
    users = User.select().sort_by(desc(User.points))
    return users


def user_exists(username):
    return exists(u for u in User if u.username == username)


def create_user(username, password):
    User(username=username, password=password)
    commit()


def update_user(id, password):
    User[id].set(password=password)
    commit()


def update_user_stats(id, points, times_exact):
    User[id].points += points
    User[id].times_exact += times_exact
    User[id].times_bet += 1
    commit()


def get_jumpers():
    jumpers = Jumpers.select()
    return jumpers


def get_jumper_by_id(id):
    jumper = Jumpers.get(lambda j: j.id == id)
    return jumper


def get_jumper_by_name(name):
    jumper = Jumpers.get(lambda j: j.name == name)
    return jumper


def create_jumper(name):
    Jumpers(name=name)
    commit()


def update_jumper(id, name):
    Jumpers[id].set(name=name)
    commit()


def delete_jumper(id):
    Jumpers[id].delete()
    commit()


def get_countries():
    countries = Countries.select()
    return countries


def get_country_by_name(name):
    country = Countries.get(lambda x: x.name == name)
    return country


def create_country(name):
    Countries(name=name)
    commit()


def bet_places_individual(first, second, third, id, update=True):
    if update:
        first_place = FirstPlaces.get(lambda x: x.bet_id.id == id)
        second_place = SecondPlaces.get(lambda x: x.bet_id.id == id)
        third_place = ThirdPlaces.get(lambda x: x.bet_id.id == id)
        first_place.set(jumper_id=first.id)
        second_place.set(jumper_id=second.id)
        third_place.set(jumper_id=third.id)
    else:
        FirstPlaces(bet_id=id, jumper_id=first.id)
        SecondPlaces(bet_id=id, jumper_id=second.id)
        ThirdPlaces(bet_id=id, jumper_id=third.id)


def bet_places_team(first, second, third, id, update=True):
    if update:
        first_place = FirstPlaces.get(lambda x: x.bet_id == id)
        second_place = SecondPlaces.get(lambda x: x.bet_id == id)
        third_place = ThirdPlaces.get(lambda x: x.bet_id == id)
        first_place.set(jumper_id=first.id)
        second_place.set(jumper_id=second.id)
        third_place.set(jumper_id=third.id)
    else:
        FirstPlaces(bet_id=id, country_id=first.id)
        SecondPlaces(bet_id=id, country_id=second.id)
        ThirdPlaces(bet_id=id, country_id=third.id)


def get_countries_tba():
    tba = Countries.get(lambda c: c.name == 'TBA')
    if tba:
        return tba
    else:
        tba = Countries(name='TBA')
        commit()
        return tba


def get_jumpers_tba():
    tba = Jumpers.get(lambda j: j.name == 'TBA')
    if tba:
        return tba
    else:
        tba = Jumpers(name='TBA')
        commit()
        return tba


def add_to_first_ten(tournament_id, name):
    jumper = get_jumper_by_name(name)
    FirstTen(tournament_id=tournament_id, jumper_id=jumper.id)


def add_to_second_ten(tournament_id, name):
    jumper = get_jumper_by_name(name)
    SecondTen(tournament_id=tournament_id, jumper_id=jumper.id)


def add_to_third_ten(tournament_id, name):
    jumper = get_jumper_by_name(name)
    ThirdTen(tournament_id=tournament_id, jumper_id=jumper.id)


def add_to_first_five(tournament_id, name):
    country = get_country_by_name(name)
    FirstFive(tournament_id=tournament_id, country_id=country.id)


def add_to_second_five(tournament_id, name):
    country = get_country_by_name(name)
    SecondFive(tournament_id=tournament_id, country_id=country.id)


def add_to_third_five(tournament_id, name):
    country = get_country_by_name(name)
    ThirdFive(tournament_id=tournament_id, country_id=country.id)


def get_tens_for_tournament(id):
    first_ten = FirstTen.select(lambda x: x.tournament_id.id == id)
    second_ten = SecondTen.select(lambda x: x.tournament_id.id == id)
    third_ten = ThirdTen.select(lambda x: x.tournament_id.id == id)
    first_ten = [x.jumper_id for x in first_ten]
    second_ten = [x.jumper_id for x in second_ten]
    third_ten = [x.jumper_id for x in third_ten]
    return [first_ten, second_ten, third_ten]


def get_fives_for_tournament(id):
    first_five = FirstFive.select(lambda x: x.tournament_id.id == id)
    second_five = SecondFive.select(lambda x: x.tournament_id.id == id)
    third_five = ThirdFive.select(lambda x: x.tournament_id.id == id)
    fives = []
    if first_five:
        fives.append([x.country_id for x in first_five])
    if second_five:
        fives.append([x.country_id for x in second_five])
    if third_five:
        fives.append([x.country_id for x in third_five])
    return fives

