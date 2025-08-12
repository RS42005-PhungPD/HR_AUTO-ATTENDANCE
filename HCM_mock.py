import json
from datetime import datetime, timedelta
import requests


def load_last_punch_time():
    """Load last punch time from JSON file"""
    try:
        with open('/home/dat/PycharmProjects/get_list_user(selenium for windows)/last_punch_time.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"att_date": "01-01-2000", "punch_time": "00:00", "emp_code": ""}


def save_last_punch_time(att_date, punch_time, emp_code):
    """Save the most recent punch time to JSON (minus 2 hours, with logging)"""
    # Parse theo định dạng dd-MM-YYYY vì dữ liệu của bạn là 13-08-2025
    original_dt = datetime.strptime(f"{att_date} {punch_time}", "%d-%m-%Y %H:%M")
    adjusted_dt = original_dt - timedelta(hours=2)

    # Log ra console
    print(f"[Original Time] {original_dt.strftime('%d-%m-%Y %H:%M')} - {emp_code}")
    print(f"[Adjusted Time] {adjusted_dt.strftime('%d-%m-%Y %H:%M')} - {emp_code}")

    # Lưu giờ đã trừ 2h
    data = {
        "att_date": adjusted_dt.strftime("%d-%m-%Y"),
        "punch_time": adjusted_dt.strftime("%H:%M"),
        "emp_code": emp_code
    }

    with open('/home/dat/PycharmProjects/get_list_user(selenium for windows)/last_punch_time.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Updated last punch time in file: {data['att_date']} {data['punch_time']} - {emp_code}")




def process_new_records(data):
    """Process and filter new records"""
    last_punch = load_last_punch_time()
    print(
        f"Last punch time: {last_punch['att_date']} {last_punch['punch_time']} - {last_punch.get('emp_code', '')}")

    new_records = []
    latest_datetime = None
    latest_record = None

    # Tạo datetime thực tế của last_punch để so sánh
    last_punch_datetime = datetime.strptime(f"{last_punch['att_date']} {last_punch['punch_time']}", "%d-%m-%Y %H:%M")

    for record in data['data']:
        record_datetime = datetime.strptime(f"{record['att_date']} {record['punch_time']}", "%d-%m-%Y %H:%M")

        # So sánh trực tiếp với datetime thực tế của last_punch
        if record_datetime > last_punch_datetime:
            new_records.append(record)

            if latest_datetime is None or record_datetime > latest_datetime:
                latest_datetime = record_datetime
                latest_record = record
        elif record_datetime == last_punch_datetime:
            # Kiểm tra duplicate cho cùng datetime
            if record['emp_code'] == last_punch.get('emp_code', ''):
                print(f"Skipping duplicate: {record['emp_code']} - {record['att_date']}")
                continue
            else:
                # Cùng thời gian nhưng khác nhân viên - vẫn là record mới
                new_records.append(record)

                if latest_datetime is None or record_datetime > latest_datetime:
                    latest_datetime = record_datetime
                    latest_record = record

    success = call_api(new_records)

    if success and latest_record:
        save_last_punch_time(latest_record['att_date'], latest_record['punch_time'], latest_record['emp_code'])

    print_result(new_records)


def call_api(new_records):
    url = "http://171.244.133.113:3293/api/cham_cong_van_tay_v2/"
    headers = {'Content-Type': 'application/json'}
    device_name = 'HCM'

    for row in new_records:
        try:
            att_date = row['att_date']
            punch_time = row['punch_time']
            timestamp = datetime.strptime(f"{att_date} {punch_time}", "%d-%m-%Y %H:%M").strftime(
                "%Y-%m-%d %H:%M:%S")
            payload = {'msnv': row['emp_code'], 'kihieumay': device_name, 'timestamp': timestamp}

            res = requests.post(url, headers=headers, json=payload)
            print("Call success", row['emp_code'])
            if res.status_code != 200:
                print(f"Error {res.status_code}: {res.text}")
                return False
        except Exception as e:
            print(f"Exception on row {row['id']}: {e}")
            return False
    return True


def print_result(new_records):
    print(f"Found {len(new_records)} new records:")
    for i, record in enumerate(new_records, 1):
        print(
            f"{i}. {record['first_name']} ({record['emp_code']}) - {record['att_date']} {record['punch_time']}")

with open('/home/dat/PycharmProjects/get_list_user(selenium for windows)/records.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(process_new_records(data))