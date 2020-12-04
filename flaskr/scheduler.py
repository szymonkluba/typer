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


def with_logging(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print('LOG: Running job "%s"' % func.__name__, flush=True)
        result = func(*args, **kwargs)
        print('LOG: Job "%s" completed' % func.__name__, flush=True)
        return result

    return wrapper


@with_logging
def close_tournament(tournament, status):
    with db_session:
        pony_db.update_tournament_status(tournament.id, status)
        body = f'{tournament.place} - {tournament.type}\n' \
               f'{datetime.strftime(tournament.date_time, "%d.%m.%Y")} ' \
               f'godzina: {tournament.datetime.strftime(tournament.date_time, "%H:%M")}'
        pony_db.new_info('warning', 'Zamknięto typowanie zawodów', body)
        pony_db.open_next_tournament()
    return schedule.CancelJob


def print_something():
    print("something")


@with_logging
def kill_task():
    sys.exit()


@with_logging
def new_tournaments():
    check_new_tournaments()


@with_logging
def tournament_updates():
    check_tournament_updates()


@with_logging
def new_qualifications():
    check_new_qualifications()


@with_logging
def participants(qualifications):
    with db_session:
        get_participants(qualifications)


now = datetime.now()
with db_session:
    current_tournament = pony_db.get_tournament_by_status("następne")
    qualifications = pony_db.select_qualifications_by_date(now)
with db_session:
    if qualifications:
        schedule.every().day.at("11:00").do(participants, qualifications=qualifications).tag('checking_participants')
        print(f'{datetime.now().strftime("%H:%M")} - Scheduled checking of participants updates', flush=True)
        for i in range(1, 13):
            time_schedule = f'{13 + (i // 4)}:{15 * (i % 4) if i % 4 != 0 else "00"}'
            schedule.every().day.at(time_schedule).do(participants, qualifications=qualifications).tag(
                'checking_participants')
t_date_time = current_tournament.date_time - timedelta(hours=1)
if now.year == t_date_time.year and now.month == t_date_time.month and now.day == t_date_time.day:
    schedule.every().day.at(datetime.strftime(t_date_time, "%H:%M")).do(close_tournament,
                                                                        tournament=current_tournament,
                                                                        status='koniec')
    time_start = t_date_time + timedelta(hours=2, minutes=10)
    time_finish = time_start
    time_start = datetime.strftime(time_start, "%H:%M")
    schedule.every().day.at(time_start).do(get_results).tag("checking_results")
    print(f'{datetime.now().strftime("%H:%M")} - Scheduled checking of results', flush=True)
    for _ in range(18):
        time_finish = t_date_time + timedelta(minutes=10)
        time_finish_S = datetime.strftime(time_finish, "%H:%M")
        schedule.every().day.at(time_finish_S).do(get_results).tag("checking_results")
schedule.every().day.at("07:00").do(tournament_updates)
print(f'{datetime.now().strftime("%H:%M")} - Scheduled checking of tournaments updates', flush=True)
schedule.every().day.at("07:15").do(new_tournaments)
print(f'{datetime.now().strftime("%H:%M")} - Scheduled checking of new tournaments', flush=True)
schedule.every().day.at("01:00").do(kill_task)
print(f'{datetime.now().strftime("%H:%M")} - Scheduled kill task', flush=True)
schedule.every().day.at("07:30").do(new_qualifications)
print(f'{datetime.now().strftime("%H:%M")} - Scheduled checking new qualifications', flush=True)
if schedule.jobs:
    for job in schedule.jobs:
        print(job, flush=True)

while True:
    schedule.run_pending()
    time.sleep(1)
