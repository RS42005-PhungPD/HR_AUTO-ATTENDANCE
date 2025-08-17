from datetime import datetime, timedelta
import json
from time import sleep

import schedule
import time


def load_last_punch_time():
    """Load last punch time from JSON file"""
    try:
        with open('/home/dat/PycharmProjects/HR_AUTO-ATTENDANCE/last_punch_time.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"att_date": "01-01-2000", "punch_time": "00:00", "emp_code": ""}


def conditional_work(last_info, default_last):
    today = datetime.now().date()
    if last_info["att_date"] == default_last["att_date"]:
        start = today - timedelta(days=6)
    else:
        last_date = datetime.strptime(last_info["att_date"], "%d-%m-%Y").date()
        start = max(last_date, today - timedelta(days=6))
    return today, start


def fetch_and_process(default_last):
    now = datetime.now()
    print(f"Running task at {now:%Y-%m-%d %H:%M:%S}")
    last_info = load_last_punch_time()
    today, start = conditional_work(last_info, default_last)
    print(today)
    print(start)

    error_count = 0
    MAX_ERRORS = 3

    while start <= today:
        params = {
            "page": 1,
            "page_size": 500,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": start.strftime("%Y-%m-%d"),
            "departments": 1,
            "areas": -1,
            "groups": -1,
            "employees": -1,
        }

        try:
            sleep(5)
            print(params)
            error_count = 0
            start += timedelta(days=1)

        except Exception as e:
            error_count += 1
            print(f"Error #{error_count}: {e!r}")
            if error_count >= MAX_ERRORS:
                print(f"Quá {MAX_ERRORS} lỗi liên tiếp. Dừng vòng lặp.")
                break


if __name__ == '__main__':
    DEFAULT_LAST = {"att_date": "01-01-2000", "punch_time": "00:00", "emp_code": ""}

    fetch_and_process(DEFAULT_LAST)
    schedule.every(5).minutes.do(fetch_and_process, DEFAULT_LAST)

    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    finally:
        pass
