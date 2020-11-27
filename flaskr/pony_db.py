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
    created = Required(datetime)
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

with db_session:
    u1 = select(u.bets for u in User)
    show(u1)



