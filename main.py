import json
import os
import time
from datetime import datetime, timedelta

import schedule
import requests
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ✅ Use a more stable approach for Windows
try:
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.core.utils import ChromeType

    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
    print("⚠️ webdriver-manager not available, falling back to manual setup")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_chrome_driver_service():
    """Get ChromeDriver service reliably"""
    if WEBDRIVER_MANAGER_AVAILABLE:
        try:
            print("🔄 Downloading ChromeDriver...")
            driver_path = ChromeDriverManager(cache_valid_range=1).install()

            if not driver_path.endswith('chromedriver.exe'):
                driver_dir = os.path.dirname(driver_path)
                for root, dirs, files in os.walk(driver_dir):
                    for file in files:
                        if file == 'chromedriver.exe':
                            driver_path = os.path.join(root, file)
                            break

            print(f"✅ ChromeDriver path: {driver_path}")
            return Service(driver_path)

        except Exception as e:
            print(f"❌ webdriver-manager failed: {e}")
            print("🔄 Trying alternative approach...")
            try:
                return Service()
            except Exception as e2:
                print(f"❌ Selenium Manager failed: {e2}")
                raise RuntimeError("Cannot setup ChromeDriver. Please install manually.")
    else:
        return Service()


class SeleniumLogin:
    def __init__(self, base_url, username, password):
        try:
            service = get_chrome_driver_service()
            opts = webdriver.ChromeOptions()
            opts.add_argument('--headless')
            opts.add_argument('--disable-gpu')
            opts.add_argument('--no-sandbox')
            opts.add_argument('--ignore-certificate-errors')
            opts.add_argument('--disable-dev-shm-usage')

            self.driver = webdriver.Chrome(service=service, options=opts)
            self.base_url = base_url
            self.username = username
            self.password = password
            print("✅ ChromeDriver initialized successfully")

        except Exception as e:
            print(f"❌ Failed to initialize ChromeDriver: {e}")
            print("💡 Solutions:")
            print("1. Update Chrome browser to latest version")
            print("2. Run: pip install --upgrade selenium webdriver-manager")
            print("3. Try manual ChromeDriver installation")
            raise

    def login(self):
        self.driver.get(self.base_url)
        wait = WebDriverWait(self.driver, 10)
        username_fake = wait.until(EC.presence_of_element_located((By.ID, "id_usernameTip")))
        username_fake.click()

        username_input = wait.until(EC.presence_of_element_located((By.ID, "id_username")))
        username_input.send_keys(self.username)

        password_fake = wait.until(EC.presence_of_element_located((By.ID, "id_passwordTip")))
        password_fake.click()

        password_input = wait.until(EC.element_to_be_clickable((By.ID, "id_password")))
        password_input.send_keys(self.password)

        check_box = wait.until(EC.presence_of_element_located((By.ID, "id_check_agreement")))
        check_box.click()

        login_button = wait.until(EC.presence_of_element_located((By.ID, "id_login")))
        login_button.click()

        wait.until(EC.url_changes(self.base_url))
        print("✅ Logged in, session alive.")


class TransactionService:
    def __init__(self, driver, base_url, last_punch_time):
        self.driver = driver
        self.base_url = base_url
        self.last_punch_time = last_punch_time

    def get_session_cookies(self):
        """Get cookies from Selenium driver to use in requests"""
        selenium_cookies = self.driver.get_cookies()
        cookies = {}
        for cookie in selenium_cookies:
            cookies[cookie['name']] = cookie['value']
        return cookies

    '''
        def get_transactions(self, params: dict):
        params_json = json.dumps(params)
        script = """
        const callback = arguments[arguments.length - 1];
        const base = arguments[0];
        const params = JSON.parse(arguments[1]);
        const body = new URLSearchParams(params).toString();

        fetch(base + "/attTransaction.do", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest"
            },
            body: body
        })
        .then(res => {
            if (!res.ok) throw new Error("HTTP " + res.status);
            return res.json();
        })
        .then(data => callback(JSON.stringify({ ok: true, data })))
        .catch(err => callback(JSON.stringify({ ok: false, error: err.toString() })));
        """
        result_str = self.driver.execute_async_script(script, self.base_url, params_json)
        result = json.loads(result_str)

        if not result.get("ok"):
            raise RuntimeError("Fetch error: " + result.get("error", "unknown"))
        return result["data"]
    '''

    def get_session_headers(self):
        """Get headers for API requests"""
        return {
            'User-Agent': self.driver.execute_script("return navigator.userAgent;"),
            'Referer': self.base_url,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        }

    def load_last_punch_time(self):
        """Load last punch time from JSON file"""
        try:
            with open(self.last_punch_time, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"att_date": "01-01-2000", "punch_time": "00:00", "emp_code": ""}

    def save_last_punch_time(self, att_date, punch_time, emp_code):
        """Save the most recent punch time to JSON (minus 2 hours, with logging)"""
        # Parse format dd-MM-YYYY
        original_dt = datetime.strptime(f"{att_date} {punch_time}", "%d-%m-%Y %H:%M")
        adjusted_dt = original_dt - timedelta(hours=2)

        print(f"[Original Time] {original_dt.strftime('%d-%m-%Y %H:%M')} - {emp_code}")
        print(f"[Adjusted Time] {adjusted_dt.strftime('%d-%m-%Y %H:%M')} - {emp_code}")

        data = {
            "att_date": adjusted_dt.strftime("%d-%m-%Y"),
            "punch_time": adjusted_dt.strftime("%H:%M"),
            "emp_code": emp_code
        }
        with open(self.last_punch_time, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"Updated last punch time in file: {data['att_date']} {data['punch_time']} - {emp_code}")

    def process_new_records(self, data):
        """Process and filter new records"""
        last_punch = self.load_last_punch_time()
        print(
            f"Last punch time: {last_punch['att_date']} {last_punch['punch_time']} - {last_punch.get('emp_code', '')}")

        new_records = []
        latest_datetime = None
        latest_record = None

        # Tạo datetime thực tế của last_punch để so sánh
        last_punch_datetime = datetime.strptime(f"{last_punch['att_date']} {last_punch['punch_time']}",
                                                "%d-%m-%Y %H:%M")

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
                    print(f"Skipping duplicate: {record['emp_code']} - {record['att_date']} {record['punch_time']}")
                    continue
                else:
                    # Cùng thời gian nhưng khác nhân viên - vẫn là record mới
                    new_records.append(record)

                    if latest_datetime is None or record_datetime > latest_datetime:
                        latest_datetime = record_datetime
                        latest_record = record

        success = self.call_api(new_records)

        if success and latest_record:
            self.save_last_punch_time(latest_record['att_date'], latest_record['punch_time'], latest_record['emp_code'])

        self.print_result(new_records)

    @staticmethod
    def call_api(new_records):
        url = "http://171.244.133.113:3293/api/cham_cong_van_tay_v2/"
        headers = {'Content-Type': 'application/json'}
        device_name = 'DPS2'

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

    @staticmethod
    def print_result(new_records):
        print(f"Found {len(new_records)} new records:")
        for i, record in enumerate(new_records, 1):
            print(
                f"{i}. {record['first_name']} ({record['emp_code']}) - {record['att_date']} {record['punch_time']} - {record['punch_state']}")


def fetch_and_process(service: TransactionService, login_by_selenium: SeleniumLogin):
    now = datetime.now()
    print(f"Running task at {now:%Y-%m-%d %H:%M:%S}")
    start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59)
    params = {
        "page": 1,
        "page_size": 500,
        "start_date": start.strftime('%Y-%m-%d'),
        "end_date": end.strftime('%Y-%m-%d'),
        "departments": 1,
        "areas": -1,
        "groups": -1,
        "employees": -1,
    }

    try:
        cookies = service.get_session_cookies()
        headers = service.get_session_headers()

        print(f"Using cookies: {list(cookies.keys())}")

        response = requests.get(
            "http://127.0.0.1:81/att/api/transactionReport/",
            params=params,
            cookies=cookies,
            headers=headers,
            verify=False
        )
        response.raise_for_status()
        data = response.json()
        service.process_new_records(data)

    except requests.RequestException as e:
        print("Error when calling API:", e)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        service.driver.refresh()
        print("🔄 Re-logging in...")
        login_by_selenium.login()
        print("✅ Re-login successful")


if __name__ == '__main__':
    LOGIN_URL = "http://127.0.0.1:81"
    USERNAME = "RscDSP2"
    PASSWORD = "RscIT@1207"
    LAST_PUNCH_FILE = r"C:\HR_ATT\DPS2_ATT\last_punch_time.json"

    login = SeleniumLogin(LOGIN_URL, USERNAME, PASSWORD)
    login.login()
    time.sleep(5)
    svc = TransactionService(login.driver, LOGIN_URL, LAST_PUNCH_FILE)

    fetch_and_process(svc, login)
    schedule.every(5).minutes.do(fetch_and_process, svc, login)

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    finally:
        login.driver.quit()
