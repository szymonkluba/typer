import functools
import sys

import schedule
import time
from pony.orm import db_session
from datetime import datetime, timedelta
from home.szymonkluba.mysite.typer.flaskr.fis_scraping import get_results, check_new_tournaments, check_tournament_updates
import home.szymonkluba.mysite.typer.flaskr.pony_db as pony_db


def with_logging(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print('LOG: Running job "%s"' % func.__name__)
        result = func(*args, **kwargs)
        print('LOG: Job "%s" completed' % func.__name__)
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


now = datetime.now()
with db_session:
    current_tournament = pony_db.get_tournament_by_status("następne")
t_date_time = current_tournament.date_time
if now.year == t_date_time.year and now.month == t_date_time.month and now.day == t_date_time.day:
    schedule.every().day.at(datetime.strftime(t_date_time, "%H:%M")).do(close_tournament,
                                                                        tournament=current_tournament,
                                                                        status='koniec')
    time_start = t_date_time + timedelta(hours=2, minutes=10)
    time_finish = time_start
    time_start = datetime.strftime(time_start, "%H:%M")
    schedule.every().day.at(time_start).do(get_results).tag("checking_results")
    print(f'{datetime.now().strftime("%H:%M")} - Scheduled checking of results')
    for _ in range(18):
        time_finish = t_date_time + timedelta(minutes=10)
        time_finish_S = datetime.strftime(time_finish, "%H:%M")
        schedule.every().day.at(time_finish_S).do(get_results).tag("checking_results")
schedule.every().day.at("09:00").do(tournament_updates)
print(f'{datetime.now().strftime("%H:%M")} - Scheduled checking of tournaments updates')
schedule.every().day.at("09:15").do(new_tournaments)
print(f'{datetime.now().strftime("%H:%M")} - Scheduled checking of new tournaments')
schedule.every().day.at("02:00").do(kill_task)
print(f'{datetime.now().strftime("%H:%M")} - Scheduled kill task')
if schedule.jobs:
    for job in schedule.jobs:
        print(job)

while True:
    schedule.run_pending()
    time.sleep(1)
