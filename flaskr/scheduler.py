import schedule
import time
from pony.orm import db_session
from datetime import datetime, timedelta
from flaskr.fis_scraping import get_results, check_new_tournaments
import flaskr.pony_db as pony_db


def close_tournament(id, status):
    with db_session:
        pony_db.update_tournament_status(id, status)
    return schedule.CancelJob


def print_something():
    print("something")


now = datetime.now()
with db_session:
    current_tournament = pony_db.get_tournament_by_status("następne")
t_date_time = current_tournament.date_time
if now.year == t_date_time.year and now.month == t_date_time.month and now.day == t_date_time.day:
    schedule.every().day.at(datetime.strftime(t_date_time, "%H:%M")).do(close_tournament(current_tournament.id, 'koniec'))
    time_start = t_date_time + timedelta(hours=2, minutes=10)
    time_finish = time_start
    time_start = datetime.strftime(time_start, "%H:%M")
    schedule.every().day.at("22:10").do(print_something).tag("checking_results")
    for _ in range(18):
        time_finish = t_date_time + timedelta(minutes=10)
        time_finish_S = datetime.strftime(time_finish, "%H:%M")
        schedule.every().day.at(time_finish_S).do(get_results).tag("checking_results")
schedule.every(1).hour().do(check_new_tournaments)


while True:
    schedule.run_pending()
    time.sleep(1)