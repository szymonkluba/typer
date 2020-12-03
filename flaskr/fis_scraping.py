from lxml import html
from pony.orm import *
from schedule import clear
import requests
import flaskr.pony_db as pony_db
import flaskr.constants as constants
from datetime import datetime, timedelta

PATH_RACES = 'https://www.fis-ski.com/DB/general/results.html?sectorcode=JP&raceid='
PATH_JUMPERS = 'https://www.fis-ski.com/DB/ski-jumping/biographies.html?lastname=&firstname=&sectorcode=JP&gendercode' \
               '=M&birthyear=1980-2020&skiclub=&skis=&nationcode=&fiscode=&status=O&search=true '
PATH_COLUMNS_HEADERS_PREF = '//*[@id="ajx_results"]/section/div/div/div/div[2]/div[1]/div/div/div/div/div['
PATH_RESULTS = '//*[@id="events-info-results"]/div/a/div/div/div['
XPATH_KIND = '//*[@class="event-header__kind"]/text()'
XPATH_SUBTITLE = '//*[@class="event-header__subtitle"]/text()'
XPATH_DATE = '//*[@class="date__full"]/text()'
XPATH_TIME = '//*[@class="time__value"]/text()'


def check_woman(field):
    if 'Women' in field[0]:
        return True
    return False


def check_children(field):
    if 'Children' in field[0]:
        return True
    return False


def check_world_cup(field):
    if 'World Cup' in field[0] or 'World Championship' in field[0]:
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
    date = tree.xpath(XPATH_DATE)
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
        subtitle = tree.xpath(XPATH_SUBTITLE)
        kind = tree.xpath(XPATH_KIND)
        time_starts = tree.xpath(XPATH_TIME)
        if not time_starts:
            break
        if not check_woman(kind) and not check_children(subtitle):
            if check_world_cup(subtitle):
                if team_or_individual(kind):
                    create_new_tournament(tree, 'drużynowe', last_fis_id, time_starts)
                else:
                    create_new_tournament(tree, 'indywidualne', last_fis_id, time_starts)


def check_tournament_updates():
    with db_session:
        tournaments = pony_db.select_tournaments_for_update()
    for tournament in tournaments:
        page = requests.get(f'{PATH_RACES}{tournament.fis_id}')
        tree = html.fromstring(page.content)
        cancelled = tree.xpath('//*[@class="event-status event-status_cancelled"]/.')
        time_starts = tree.xpath(XPATH_TIME)
        date = tree.xpath(XPATH_DATE)
        date = datetime.strptime(date[0], '%B %d, %Y')
        time_starts = time_starts[0].split(':')
        date_time = date + timedelta(hours=int(time_starts[0]), minutes=int(time_starts[1]))
        if cancelled:
            with db_session:
                pony_db.update_tournament_status(tournament.id, 'odwołane')
        if date_time != tournament.date_time:
            with db_session:
                pony_db.update_tournament_date_time(tournament.id, date_time)


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


def get_results():
    with db_session:
        tournament = pony_db.get_tournament_by_status('koniec')
    if tournament:
        page = requests.get(f'{PATH_RACES}{tournament.fis_id}')
        tree = html.fromstring(page.content)
        podium = tree.xpath('//*[@class="result-card__name"]/text()')
        if podium:
            for i in range(len(podium)):
                podium[i] = podium[i].replace('\n', '').strip()
                if podium[i] in constants.COUNTRIES.keys():
                    podium[i] = constants.COUNTRIES[podium[i]]
            podium = [x for x in podium if x != '']
            with db_session:
                pony_db.update_tournament_podium(tournament.id, tournament.type, *podium)
            column_index = 1
            column = tree.xpath(f'{PATH_COLUMNS_HEADERS_PREF}{column_index}]/text()')[0]
            while column != 'Athlete' and column != 'Name':
                column_index += 1
                column = tree.xpath(f'{PATH_COLUMNS_HEADERS_PREF}{column_index}]/text()')[0]
            if tournament.type == 'drużynowe':
                results = tree.xpath(f'{PATH_RESULTS}{column_index}]/text()')
                results_team = []
                for result in results:
                    result = result.replace('\n', '').strip()
                    if result in constants.COUNTRIES:
                        results_team.append(result)
                with db_session:
                    for i in range(len(results_team)):
                        if i < 5:
                            pony_db.add_to_first_five(tournament.id, constants.COUNTRIES[results_team[i]])
                        elif i < 10:
                            pony_db.add_to_second_five(tournament.id, constants.COUNTRIES[results_team[i]])
                        elif i < 15:
                            pony_db.add_to_third_five(tournament.id, constants.COUNTRIES[results_team[i]])
            else:
                results = tree.xpath(f'{PATH_RESULTS}{column_index}]/text()')
                with db_session:
                    for i in range(len(results)):
                        results[i] = results[i].replace('\n', '').strip()
                        if i < 10:
                            pony_db.add_to_first_ten(tournament.id, results[i])
                        elif i < 20:
                            pony_db.add_to_second_ten(tournament.id, results[i])
                        elif i < 30:
                            pony_db.add_to_third_ten(tournament.id, results[i])
            clear("checking_results")


check_tournament_updates()

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
