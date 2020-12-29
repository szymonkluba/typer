from lxml import html
from pony.orm import db_session
from schedule import clear
import requests
import typer.pony_db as pony_db
import typer.constants as constants
from typer.points import calculate_points
from datetime import datetime, timedelta
from typer.logging_wrapper import with_logging

PATH_RACES = 'https://www.fis-ski.com/DB/general/results.html?sectorcode=JP&raceid='
PATH_JUMPERS = 'https://www.fis-ski.com/DB/ski-jumping/biographies.html?lastname=&firstname=&sectorcode=JP&gendercode' \
               '=M&birthyear=1980-2020&skiclub=&skis=&nationcode=&fiscode=&status=O&search=true '
PATH_COLUMNS_HEADERS_QUAL = '//*[@id="ajx_results"]/section/div/div/div/div/div[1]/div/div/div/div/div['
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


def check_qualifications(field):
    if 'Viessmann' in field[0] and 'Qualification' in field[0]:
        return True
    return False


def team_or_individual(field):
    if 'Team' in field[0]:
        return True
    return False


@with_logging
@db_session
def create_new_tournament(tree, typ, fis_id, time_starts):
    place = tree.xpath('//*[@class="event-header__name heading_off-sm-style"]/h1/text()')
    place = place[0].replace('\n', '').strip()
    place = place[:place.index(' (')]
    date = tree.xpath(XPATH_DATE)
    date = datetime.strptime(date[0], '%B %d, %Y')
    time_starts = time_starts[0].split(':')
    date_time = date + timedelta(hours=int(time_starts[0]), minutes=int(time_starts[1]))
    pony_db.create_tournament(place, typ, 'przyszłe', date_time, fis_id)
    body = f'{place} - {typ}\n' \
           f'{datetime.strftime(date_time, "%d.%m.%Y")} godzina: {datetime.strftime(date_time, "%H:%M")}'
    pony_db.new_info('info', 'Nowe zawody', body)


@with_logging
@db_session
def check_new_tournaments():
    last_fis_id = pony_db.get_last_fis_id()
    for fis_id in range(last_fis_id, 5900):
        if not pony_db.fis_id_exists(fis_id):
            page = requests.get(f'{PATH_RACES}{fis_id}')
            tree = html.fromstring(page.content)
            time_starts = tree.xpath(XPATH_TIME)
            if not time_starts:
                continue
            subtitle = tree.xpath(XPATH_SUBTITLE)
            kind = tree.xpath(XPATH_KIND)
            if not check_woman(kind) and not check_children(subtitle):
                if check_world_cup(subtitle):
                    if team_or_individual(kind):
                        create_new_tournament(tree, 'drużynowe', fis_id, time_starts)
                    else:
                        create_new_tournament(tree, 'indywidualne', fis_id, time_starts)
            last_fis_id += 1


@with_logging
@db_session
def check_tournament_updates():
    tournaments = pony_db.Tournaments.select(lambda t: t.status in ('następne', 'przyszłe', 'odwołane'))
    for tournament in tournaments:
        page = requests.get(f'{PATH_RACES}{tournament.fis_id}')
        tree = html.fromstring(page.content)
        cancelled = tree.xpath('//*[@class="event-status event-status_cancelled"]/.')
        time_starts = tree.xpath(XPATH_TIME)
        date = tree.xpath(XPATH_DATE)
        date = datetime.strptime(date[0], '%B %d, %Y')
        time_starts = time_starts[0].split(':')
        date_time = date + timedelta(hours=int(time_starts[0]), minutes=int(time_starts[1]))
        if cancelled and tournament.status != 'odwołane':
            tournament.set(status='odwołane')
            body = f'{tournament.place} - {tournament.type}\n' \
                   f'{datetime.strftime(tournament.date_time, "%d.%m.%Y")} ' \
                   f'godzina: {datetime.strftime(tournament.date_time, "%H:%M")}'
            pony_db.new_info('danger', 'Zawody odwołane', body)
            print(f'LOG: Tournament cancelled {tournament.place} {tournament.date_time}', flush=True)
        elif not cancelled and tournament.status == 'odwołane':
            tournament.set(status='przyszłe')
            body = f'{tournament.place} - {tournament.type}\n' \
                   f'{datetime.strftime(tournament.date_time, "%d.%m.%Y")} ' \
                   f'godzina: {datetime.strftime(tournament.date_time, "%H:%M")}'
            pony_db.new_info('success', 'Odwołane zawody przywrócone', body)
            print(f'LOG: Cancelled tournament rescheduled', flush=True)
        if date_time != tournament.date_time:
            tournament.set(date_time=date_time)
            body = f'{tournament.place} - {tournament.type}\n' \
                   f'{datetime.strftime(date_time, "%d.%m.%Y")} ' \
                   f'godzina: {datetime.strftime(date_time, "%H:%M")}'
            pony_db.new_info('warning', 'Zmiana terminu rozpoczęcia', body)
            print(f'LOG: Tournament rescheduled', flush=True)


@with_logging
@db_session
def get_active_jumpers():
    page = requests.get(PATH_JUMPERS)
    tree = html.fromstring(page.content)
    list_of_jumpers = tree.xpath('//*[@id="athletes-search"]/div/a/div/div[2]/text()')
    for jumper in list_of_jumpers:
        pony_db.Jumpers(name=jumper)


@with_logging
@db_session
def get_countries_from_list():
    for country in constants.COUNTRIES.values():
        pony_db.Countries(name=country)


@with_logging
@db_session
def get_results():
    tournaments = pony_db.Tournaments.select(lambda t: t.status == "koniec")
    if tournaments:
        for tournament in tournaments:
            page = requests.get(f'{PATH_RACES}{tournament.fis_id}')
            tree = html.fromstring(page.content)
            podium = tree.xpath('//*[@class="result-card__name"]/text()')
            if podium:
                for i in range(len(podium)):
                    podium[i] = podium[i].replace('\n', '').strip()
                    if podium[i] in constants.COUNTRIES.keys():
                        podium[i] = constants.COUNTRIES[podium[i]]
                podium = [x for x in podium if x != '']
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
                    for i in range(len(results_team)):
                        if i < 5:
                            pony_db.add_to_first_five(tournament.id, constants.COUNTRIES[results_team[i]])
                        elif i < 10:
                            pony_db.add_to_second_five(tournament.id, constants.COUNTRIES[results_team[i]])
                        elif i < 15:
                            pony_db.add_to_third_five(tournament.id, constants.COUNTRIES[results_team[i]])
                else:
                    results = tree.xpath(f'{PATH_RESULTS}{column_index}]/text()')
                    for i in range(len(results)):
                        results[i] = results[i].replace('\n', '').strip()
                        if i < 10:
                            pony_db.add_to_first_ten(tournament.id, results[i])
                        elif i < 20:
                            pony_db.add_to_second_ten(tournament.id, results[i])
                        elif i < 30:
                            pony_db.add_to_third_ten(tournament.id, results[i])
                body = f'{tournament.place} - {tournament.type}\n' \
                       f'{datetime.strftime(tournament.date_time, "%d.%m.%Y")} ' \
                       f'godzina: {datetime.strftime(tournament.date_time, "%H:%M")}'
                pony_db.new_info('success', 'Podsumowanie wyników', body)
                tournament.set(status="archiwum")
            else:
                return None
        calculate_points(tournaments)
        clear("checking_results")
    else:
        print(f"LOG: No tournament to check results")
        clear("checking_results")


@with_logging
@db_session
def check_new_qualifications():
    last_fis_id = pony_db.get_last_fis_id()
    for fis_id in range(last_fis_id, 5900):
        if not pony_db.quali_fis_id_exists(fis_id):
            page = requests.get(f'{PATH_RACES}{fis_id}')
            tree = html.fromstring(page.content)
            time_starts = tree.xpath(XPATH_TIME)
            if not time_starts:
                continue
            subtitle = tree.xpath(XPATH_SUBTITLE)
            kind = tree.xpath(XPATH_KIND)
            if not check_woman(kind) and not check_children(subtitle):
                if check_qualifications(subtitle):
                    if not team_or_individual(kind):
                        place = tree.xpath('//*[@class="event-header__name heading_off-sm-style"]/h1/text()')
                        place = place[0].replace('\n', '').strip()
                        place = place[:place.index(' (')]
                        date = tree.xpath(XPATH_DATE)
                        date = datetime.strptime(date[0], '%B %d, %Y')
                        time_starts = time_starts[0].split(':')
                        date_time = date + timedelta(hours=int(time_starts[0]), minutes=int(time_starts[1]))
                        margin = date_time + timedelta(days=4)
                        for tournament in pony_db.Tournaments.select(lambda t: t.place == place):
                            if date_time < tournament.date_time < margin and tournament.type == 'indywidualne':
                                pony_db.new_qualifications(fis_id, tournament.id, date_time)


@with_logging
@db_session
def get_participants(qualifications):
    for quali in qualifications:
        page = requests.get(f'{PATH_RACES}{quali.fis_id}')
        tree = html.fromstring(page.content)
        column_index = 1
        column = tree.xpath(f'{PATH_COLUMNS_HEADERS_QUAL}{column_index}]/text()')
        if column:
            while column[0] != 'Athlete':
                column_index += 1
                column = tree.xpath(f'{PATH_COLUMNS_HEADERS_QUAL}{column_index}]/text()')
                if not column:
                    break
            participants = tree.xpath(f'{PATH_RESULTS}{column_index}]/text()')
            if participants:
                for participant in participants:
                    participant = participant.replace('\n', '').strip()
                    pony_db.new_participant(participant, quali.tournament_id)
                    clear('checking_participants')
