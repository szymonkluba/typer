import functools
import sys
import schedule
import time
from pony.orm import db_session
from datetime import datetime, timedelta

sys.path.append("/home/szymonkluba/mysite/typer/")

from flaskr.fis_scraping import (
    get_results, check_new_tournaments, check_tournament_updates, get_participants, check_new_qualifications
)
import flaskr.pony_db as pony_db
from flaskr.points import calculate_points


def with_logging(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print('LOG: Running job "%s"' % func.__name__, flush=True)
        result = func(*args, **kwargs)
        print('LOG: Job "%s" completed' % func.__name__, flush=True)
        return result

    return wrapper


def print_schedule():
    if schedule.jobs:
        for job in schedule.jobs:
            print(job, flush=True)


@with_logging
@db_session
def close_tournament(tournament, status):
    pony_db.update_tournament_status(tournament.id, status)
    body = f'{tournament.place} - {tournament.type}\n' \
               f'{datetime.strftime(tournament.date_time, "%d.%m.%Y")} ' \
               f'godzina: {datetime.strftime(tournament.date_time, "%H:%M")}'
    pony_db.new_info('warning', 'Zamknięto typowanie zawodów', body)
    pony_db.open_next_tournament()
    schedule.clear('closing_tournament')
    print_schedule()


def print_something():
    print("something")


@with_logging
@db_session
def new_tournaments():
    check_new_tournaments()
    print_schedule()


@with_logging
@db_session
def tournament_updates():
    check_tournament_updates()
    print_schedule()


@with_logging
@db_session
def new_qualifications():
    check_new_qualifications()
    print_schedule()


@with_logging
@db_session
def participants(qualifications):
    get_participants(qualifications)
    print_schedule()


@with_logging
@db_session
def points():
    calculate_points()


@with_logging
def schedule_result_checking():
    schedule.every(5).minutes.do(get_results).tag("checking_results")
    schedule.clear("schedule_results")


def schedule_participants_checking(qualifications):
    schedule.every(15).minutes.do(participants, qualifications=qualifications).tag('checking_participants')
    schedule.clear("schedule_participants")


@with_logging
@db_session
def is_tournament_today():
    now = datetime.now()
    current_tournament = pony_db.get_tournament_by_status("następne")
    t_date_time = current_tournament.date_time - timedelta(hours=1)
    if now.date() == t_date_time.date():
        schedule.every().day.at(datetime.strftime(t_date_time, "%H:%M")).do(close_tournament,
                                                                            tournament=current_tournament,
                                                                            status='koniec').tag("closing_tournament")
        print(f'LOG: {datetime.now().strftime("%H:%M")} - Scheduled closing of tournament', flush=True)
        time_start = t_date_time + timedelta(hours=1, minutes=30)
        time_start = datetime.strftime(time_start, "%H:%M")
        schedule.every().day.at(time_start).do(schedule_result_checking).tag("schedule_results")


@with_logging
@db_session
def is_qualification_today():
    now = datetime.now()
    qualifications = pony_db.select_qualifications_by_date(now)
    delta = 1
    if qualifications:
        for q in qualifications:
            t_date_time = q.date_time + timedelta(minutes=delta)
            delta += 2
            time_string = datetime.strftime(t_date_time, "%H:%M")
            schedule.every().day.at(time_string).do(schedule_participants_checking,
                                                    qualifications=qualifications).tag('schedule_participants')
            print(f'LOG: {datetime.now().strftime("%H:%M")} - Scheduled checking of participants updates', flush=True)


schedule.every().day.at("08:00").do(is_tournament_today)
print(f'LOG: {datetime.now().strftime("%H:%M")} - Scheduled checking of tournament happening', flush=True)
schedule.every().day.at('08:10').do(is_qualification_today)
print(f'LOG: {datetime.now().strftime("%H:%M")} - Scheduled checking of qualifications happening', flush=True)
schedule.every(3).hours.do(tournament_updates)
print(f'LOG: {datetime.now().strftime("%H:%M")} - Scheduled checking of tournaments updates', flush=True)
schedule.every().day.at("08:35").do(new_tournaments)
print(f'LOG: {datetime.now().strftime("%H:%M")} - Scheduled checking qualifications', flush=True)
schedule.every().day.at("08:40").do(new_qualifications)
print(f'LOG: {datetime.now().strftime("%H:%M")} - Scheduled checking new qualifications', flush=True)
print_schedule()

while True:
    schedule.run_pending()
    time.sleep(1)
