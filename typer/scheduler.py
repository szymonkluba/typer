import sys
import schedule
import time
from pony.orm import db_session
from datetime import datetime, timedelta

sys.path.append("/home/szymonkluba/mysite/typer")

from typer.fis_scraping import (
    get_results,
    check_new_tournaments,
    check_tournament_updates,
    get_participants,
    check_new_qualifications,
)
import typer.pony_db as pony_db
from typer.points import calculate_points
from typer.logging_wrapper import with_logging


def print_schedule():
    if schedule.jobs:
        for job in schedule.jobs:
            print(job, flush=True)


@with_logging
@db_session
def close_tournament():
    tournament = pony_db.Tournaments.get(lambda t: t.status == "następne")
    tournament.set(status="koniec")
    body = f"{tournament.place} - {tournament.type}\n" \
           f"{datetime.strftime(tournament.date_time, '%d.%m.%Y')} " \
           f"godzina: {datetime.strftime(tournament.date_time, '%H:%M')}"
    pony_db.new_info("warning", "Zamknięto typowanie zawodów", body)
    pony_db.open_next_tournament()
    print(f"LOG: Tournament closed", flush=True)
    schedule.clear("closing_tournament")
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
@db_session
def schedule_result_checking():
    schedule.every(5).minutes.do(get_results).tag("checking_results")
    print("LOG: Scheduled checking of results", flush=True)
    schedule.clear("schedule_results")


@with_logging
@db_session
def schedule_participants_checking(qualifications):
    schedule.every(15).minutes.do(participants, qualifications=qualifications).tag("checking_participants")
    print("LOG: Scheduled checking of participants", flush=True)
    schedule.clear("schedule_participants")


@with_logging
@db_session
def is_tournament_today():
    now = datetime.now()
    current_tournament = pony_db.Tournaments.get(lambda t: t.status == "następne")
    t_date_time = current_tournament.date_time - timedelta(hours=1)
    if now.date() == t_date_time.date():
        time_string = datetime.strftime(t_date_time, "%H:%M")
        schedule.every().day.at(time_string).do(close_tournament).tag("closing_tournament")
        print("LOG: Scheduled closing of tournament", flush=True)
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
            t_date_time = q.date_time + timedelta(hours=-1, minutes=delta)
            delta += 2
            time_string = datetime.strftime(t_date_time, "%H:%M")
            schedule.every().day.at(time_string).do(schedule_participants_checking,
                                                    qualifications=qualifications).tag("schedule_participants")
            print("LOG: Scheduled checking of participants updates", flush=True)


if __name__ == '__main__':
    schedule_result_checking()
    schedule.every().day.at("08:00").do(is_tournament_today)
    print("LOG: Scheduled checking of tournament happening", flush=True)
    schedule.every().day.at('08:10').do(is_qualification_today)
    print("LOG: Scheduled checking of qualifications happening", flush=True)
    schedule.every(3).hours.do(tournament_updates)
    print("LOG: Scheduled checking of tournaments updates", flush=True)
    schedule.every().day.at("08:35").do(new_tournaments)
    print("LOG: Scheduled checking qualifications", flush=True)
    schedule.every().day.at("08:40").do(new_qualifications)
    print("LOG: Scheduled checking new qualifications", flush=True)
    print_schedule()

    while True:
        schedule.run_pending()
        time.sleep(1)
