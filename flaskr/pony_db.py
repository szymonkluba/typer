from pony.orm import *
from datetime import datetime

db = Database()
db.bind(provider='sqlite',
        filename='flaskr.sqlite',
        create_db=True)


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    username = Required(str, unique=True)
    password = Required(str)
    times_bet = Optional(int, default=0)
    times_exact = Optional(int, default=0)
    points = Optional(int, default=0)
    bets = Set("Bets")


class Tournaments(db.Entity):
    id = PrimaryKey(int, auto=True)
    place = Required(str)
    type = Required(str)
    date_time = Required(datetime)
    first_place = Required(str)
    second_place = Required(str)
    third_place = Required(str)
    status = Required(str)
    fis_id = Required(int)
    bets = Set('Bets')


class Bets(db.Entity):
    id = PrimaryKey(int, auto=True)
    user_id = Required(User)
    created = Required(datetime, sql_default='CURRENT_TIMESTAMP')
    first_place = Required(str)
    second_place = Required(str)
    third_place = Required(str)
    tournament_id = Required(Tournaments)
    first_ten = Set("Jumpers")
    second_ten = Set("Jumpers")
    third_ten = Set("Jumpers")


class Jumpers(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)


class Countries(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)


db.generate_mapping(create_tables=False)


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
    Bets(first_place=first_place,
         second_place=second_place,
         third_place=third_place,
         user_id=user_id,
         tournament_id=tournament_id)
    commit()


def update_bet(first_place, second_place, third_place, id):
    Bets[id].set(first_place=first_place,
                 second_place=second_place,
                 third_place=third_place)
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


def get_last_fis_id():
    fis_id = select(t.fis_id for t in Tournaments).max()
    return fis_id


def create_tournament(place, type, status, date_time, fis_id, first_place='TBA', second_place='TBA', third_place='TBA'):
    Tournaments(place=place,
                type=type,
                status=status,
                date_time=date_time,
                first_place=first_place,
                second_place=second_place,
                third_place=third_place,
                fis_id=fis_id)
    commit()


def update_tournament(id, place, type, status, date_time, first_place='TBA', second_place='TBA', third_place='TBA'):
    Tournaments[id].set(place=place,
                        type=type,
                        status=status,
                        date_time=date_time,
                        first_place=first_place,
                        second_place=second_place,
                        third_place=third_place)
    commit()


def update_tournament_status(id, status):
    Tournaments[id].set(status=status)
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


def get_jumper(id):
    jumper = Jumpers.get(lambda j: j.id == id)
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
