from lxml import html
from pony.orm import *
import requests
import flaskr.pony_db as pony_db
import flaskr.constants as constants
from datetime import datetime, timedelta

PATH_RACES = 'https://www.fis-ski.com/DB/general/results.html?sectorcode=JP&raceid='
PATH_JUMPERS = 'https://www.fis-ski.com/DB/ski-jumping/biographies.html?lastname=&firstname=&sectorcode=JP&gendercode' \
               '=M&birthyear=1980-2020&skiclub=&skis=&nationcode=&fiscode=&status=O&search=true '


def check_woman(field):
    if 'Women' in field[0]:
        return True
    return False


def check_children(field):
    if 'Children' in field[0]:
        return True
    return False


def check_world_cup(field):
    if 'World Cup' in field[0]:
        return True
    return False


def team_or_individual(field):
    if 'Team' in field[0]:
        return True
    return False


def create_new_tournament(tree, typ, fis_id, time_starts):
    place = tree.xpath('//*[@class="event-header__name heading_off-sm-style"]/h1/text()')
    place = place[0].replace('\n', '').strip()
    place = place[:place.index(' (')]
    date = tree.xpath('//*[@class="date__full"]/text()')
    date = datetime.strptime(date[0], '%B %d, %Y')
    time_starts = time_starts[0].split(':')
    date_time = date + timedelta(hours=int(time_starts[0]), minutes=int(time_starts[1]))
    with db_session():
        pony_db.create_tournament(place, typ, 'przyszłe', date_time, fis_id)


def check_new_tournaments():
    with db_session():
        last_fis_id = pony_db.get_last_fis_id()
    while True:
        last_fis_id += 1
        page = requests.get(f'{PATH_RACES}{last_fis_id}')
        tree = html.fromstring(page.content)
        subtitle = tree.xpath('//*[@class="event-header__subtitle"]/text()')
        kind = tree.xpath('//*[@class="event-header__kind"]/text()')
        time_starts = tree.xpath('//*[@class="time__value"]/text()')
        if not time_starts:
            break
        if not check_woman(kind) and not check_children(subtitle):
            if check_world_cup(subtitle):
                if team_or_individual(kind):
                    create_new_tournament(tree, 'drużynowe', last_fis_id, time_starts)
                else:
                    create_new_tournament(tree, 'indywidualne', last_fis_id, time_starts)


def get_active_jumpers():
    page = requests.get(PATH_JUMPERS)
    tree = html.fromstring(page.content)
    list_of_jumpers = tree.xpath('//*[@id="athletes-search"]/div/a/div/div[2]/text()')
    for jumper in list_of_jumpers:
        with db_session:
            pony_db.create_jumper(jumper)


def get_countries_from_list():
    for country in constants.COUNTRIES:
        with db_session:
            pony_db.create_country(country)



# for name in names_temp:
#     name = name.replace('\n', '').strip()
#     name = name.split()
#     if name[0] in DUPLICATE_SURNAMES:
#         names.append(f'{name[0]} {name[1][0]}')
#     else:
#         names.append(name[0])
# standings = [[places[i], names[i]] for i in range(len(places))]
#
# for standing in standings:
#     print(f'place: {standing[0]} name: {standing[1]}')
