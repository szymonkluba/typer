import schedule
import time
from pony.orm import db_session
from datetime import datetime, timedelta
from flaskr.fis_scraping import get_results, check_new_tournaments, check_tournament_updates
import flaskr.pony_db as pony_db


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


now = datetime.now()
check_tournament_updates()
check_new_tournaments()
with db_session:
    current_tournament = pony_db.get_tournament_by_status("następne")
t_date_time = current_tournament.date_time
if now.year == t_date_time.year and now.month == t_date_time.month and now.day == t_date_time.day:
    schedule.every().day.at(datetime.strftime(t_date_time, "%H:%M")).do(close_tournament(current_tournament,
                                                                                         'koniec'))
    time_start = t_date_time + timedelta(hours=2, minutes=10)
    time_finish = time_start
    time_start = datetime.strftime(time_start, "%H:%M")
    schedule.every().day.at(time_start).do(get_results).tag("checking_results")
    for _ in range(18):
        time_finish = t_date_time + timedelta(minutes=10)
        time_finish_S = datetime.strftime(time_finish, "%H:%M")
        schedule.every().day.at(time_finish_S).do(get_results).tag("checking_results")
schedule.every().day.at("09:00").do(check_tournament_updates())
schedule.every().day.at("09:15").do(check_new_tournaments)

while True:
    schedule.run_pending()
    time.sleep(1)
