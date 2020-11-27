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
    times_bet = Optional(int)
    times_exact = Optional(int)
    points = Optional(int)
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
    bets = Set('Bets')


class Bets(db.Entity):
    id = PrimaryKey(int, auto=True)
    user_id = Required(User)
    created = Required(datetime, sql_default='CURRENT_TIMESTAMP')
    first_place = Required(str)
    second_place = Required(str)
    third_place = Required(str)
    tournament_id = Required(Tournaments)


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
        bets = select(lambda b: b.user_id == id).sort_by(desc(Bets.created))
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
    tournaments = Tournaments.select()
    return tournaments


def get_tournament(id):
    tournament = Tournaments.get(lambda t: t.id == id)
    return tournament


def get_users():
    users = User.select()
    return users


def get_users_ranking():
    users = User.select().sort_by(desc(User.points))
    return users


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


def get_current_tournament():
    current_tournament = Tournaments.get(lambda t: t.status == 'następne')
    return current_tournament
