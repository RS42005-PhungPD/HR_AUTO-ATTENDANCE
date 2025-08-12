import json
from datetime import datetime, timedelta
import requests


def load_last_punch_time():
    """Load last punch date from JSON file"""
    try:
        with open('last_punch_time.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('last_date', '2025-01-01')
    except:
        return '2025-01-01'


def load_last_record():
    """Load last record date from JSON file"""
    try:
        with open('last_records.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('data', '')
    except:
        return ''


def save_last_date(date_str):
    """Save the most recent date to JSON"""
    data = {"last_date": date_str}
    with open('last_punch_time.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"\nUpdated last processed date: {date_str}")


def save_last_record(records):
    data = {"data": records}
    with open('last_records.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"\nUpdated last records.")


def call_api(new_records):
    url = "http://171.244.133.113:3293/api/cham_cong_van_tay_v2/"
    headers = {'Content-Type': 'application/json'}
    device_name = 'HCM'

    for row in new_records:
        try:
            att_date = row['att_date']
            clock_in = row['clock_in']
            clock_out = row['clock_out']

            time_clock = clock_out if clock_out else clock_in
            # print(f"time clock {row['emp_code']}: {time_clock}")
            timestamp_clock = datetime.strptime(f"{att_date} {time_clock}", "%Y-%m-%d %H:%M").strftime(
                "%Y-%m-%d %H:%M:%S")

            payload_in = {'msnv': row['emp_code'], 'kihieumay': device_name, 'timestamp': timestamp_clock}

            res_in = requests.post(url, headers=headers, json=payload_in)
            print("Call success", row['emp_code'])
            if res_in.status_code != 200:
                print(f"Error {res_in.status_code}: {res_in.text}")
                return False

        except Exception as e:
            print(f"Exception on row {row.get('id')}: {e}")

            return False
    return True


def process_new_records(data):
    """
    Process and filter new records based on date comparison
    """
    last_date = load_last_punch_time()
    print(f"Last processed date: {last_date}")

    new_records = []
    latest_date = None

    for record in data['data']:
        att_date = record['att_date']

        # compare day (string comparison works for YYYY-MM-DD format)
        if att_date >= last_date:
            # add record if clock_in is not None
            if record.get('clock_in') is not None:
                new_records.append(record)

            if latest_date is None or att_date > latest_date:
                latest_date = att_date

    # check vs file data
    if check_old_vs_current_records(new_records):
        return {"messages": "Not new records"}

    # success = call_api(new_records)
    success = True

    if success and latest_date:
        save_last_date(latest_date)
        save_last_record(new_records)
        print_result(new_records)
    return None
    # return new_records


def check_old_vs_current_records(new_records):
    last_records = load_last_record()
    if not last_records:
        return False
    return new_records == last_records


def print_result(new_records):
    print(f"\nFound {len(new_records)} new records:")
    for i, record in enumerate(new_records, 1):
        clock_in = record.get('clock_in') or 'None'
        clock_out = record.get('clock_out') or 'None'
        print(f"{i}. {record['emp_code']} - {record['att_date']} (IN: {clock_in}, OUT: {clock_out})")


with open('/home/dat/PycharmProjects/get_list_user(selenium for windows)/records.json', 'r', encoding='utf-8') as f:
    data = json.load(f)


print(process_new_records(data))
