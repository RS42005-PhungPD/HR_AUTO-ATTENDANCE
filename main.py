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

MANUAL_CHROMEDRIVER_PATH = r"C:\HR\AI\get_list_user(selenium for windows)\chromedriver-win64\chromedriver.exe"

# Nếu Chrome cài ở vị trí khác, uncomment và điền đường dẫn:
# MANUAL_CHROME_BINARY_PATH = r"C:\path\to\your\chrome.exe"
MANUAL_CHROME_BINARY_PATH = None

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

    # ✅ Ưu tiên sử dụng đường dẫn thủ công nếu được cấu hình
    if MANUAL_CHROMEDRIVER_PATH and os.path.exists(MANUAL_CHROMEDRIVER_PATH):
        print(f"✅ Using manual ChromeDriver path: {MANUAL_CHROMEDRIVER_PATH}")
        return Service(MANUAL_CHROMEDRIVER_PATH)

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
                print("💡 Hướng dẫn tải ChromeDriver thủ công:")
                print("1. Tải ChromeDriver từ: https://chromedriver.chromium.org/")
                print("2. Giải nén và đặt đường dẫn vào MANUAL_CHROMEDRIVER_PATH")
                print("3. Ví dụ: MANUAL_CHROMEDRIVER_PATH = r'C:\\chromedriver\\chromedriver.exe'")
                raise RuntimeError("Cannot setup ChromeDriver. Please install manually.")
    else:
        print("💡 Hướng dẫn tải ChromeDriver thủ công:")
        print("1. Tải ChromeDriver từ: https://chromedriver.chromium.org/")
        print("2. Giải nén và đặt đường dẫn vào MANUAL_CHROMEDRIVER_PATH")
        print("3. Ví dụ: MANUAL_CHROMEDRIVER_PATH = r'C:\\chromedriver\\chromedriver.exe'")
        return Service()


def get_chrome_binary_path():
    """Detect Chrome installation path on Windows"""
    import platform

    # Ưu tiên sử dụng đường dẫn thủ công nếu được cấu hình
    if MANUAL_CHROME_BINARY_PATH and os.path.exists(MANUAL_CHROME_BINARY_PATH):
        print(f"✅ Using manual Chrome binary path: {MANUAL_CHROME_BINARY_PATH}")
        return MANUAL_CHROME_BINARY_PATH

    if platform.system() != "Windows":
        return None

    # Common Chrome installation paths on Windows
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.environ.get('USERNAME', '')),
        r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome Beta\Application\chrome.exe",
    ]

    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Found Chrome at: {path}")
            return path

    print("❌ Chrome not found in common installation paths")
    return None


class SeleniumLogin:
    def __init__(self, base_url, username, password):
        try:
            service = get_chrome_driver_service()
            opts = webdriver.ChromeOptions()

            # Detect Chrome binary path
            chrome_binary = get_chrome_binary_path()
            if chrome_binary:
                opts.binary_location = chrome_binary

            opts.add_argument('--headless')
            opts.add_argument('--disable-gpu')
            opts.add_argument('--no-sandbox')
            opts.add_argument('--ignore-certificate-errors')
            opts.add_argument('--disable-dev-shm-usage')
            opts.add_argument('--disable-blink-features=AutomationControlled')
            opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            opts.add_experimental_option('useAutomationExtension', False)

            self.driver = webdriver.Chrome(service=service, options=opts)
            self.base_url = base_url
            self.username = username
            self.password = password
            print("✅ ChromeDriver initialized successfully")

        except Exception as e:
            print(f"❌ Failed to initialize ChromeDriver: {e}")
            print("💡 Solutions:")
            print("1. Install Google Chrome from: https://www.google.com/chrome/")
            print("2. Update Chrome browser to latest version")
            print("3. Run: pip install --upgrade selenium webdriver-manager")
            print("4. Check if Chrome is installed in a custom location")
            print("5. Try running without headless mode (remove --headless)")
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
    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.last_id_file = 'last_user_id.txt'

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

    @staticmethod
    def load_last_date():
        """Load last punch date from JSON file"""
        try:
            with open('last_punch_time.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('last_date', '2025-01-01')
        except:
            return '2000-01-01'

    @staticmethod
    def load_last_record():
        """Load last record date from JSON file"""
        try:
            with open('last_records.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('data', '')
        except:
            return ''

    @staticmethod
    def save_last_date(date_str):
        """Save the most recent date to JSON"""
        data = {"last_date": date_str}
        with open('last_punch_time.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\nUpdated last processed date: {date_str}")

    @staticmethod
    def save_last_record(records):
        data = {"data": records}
        with open('last_records.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\nUpdated last records.")

    def process_new_records(self, data):
        """Process and filter new records"""
        last_date = self.load_last_date()
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

        #check old record and current record
        if self.check_old_vs_current_records(new_records):
            print("Not new records.")
            return None

        self.call_api(new_records)

        if latest_date:
            self.save_last_date(latest_date)
        self.save_last_record(new_records)
        self.print_result(new_records)

    def check_old_vs_current_records(self, new_records):
        last_records = self.load_last_record()
        if not last_records:
            return False
        return new_records == last_records

    @staticmethod
    def call_api(new_records):
        url = "http://171.244.133.113:3293/api/cham_cong_van_tay_v2/"
        headers = {'Content-Type': 'application/json'}
        device_name = 'HCM'

        for row in new_records:
            try:
                att_date = row['att_date']
                clock_in = row['clock_in']
                clock_out = row['clock_out']

                timestamp_clockin = datetime.strptime(f"{att_date} {clock_in}", "%Y-%m-%d %H:%M").strftime(
                    "%Y-%m-%d %H:%M:%S")
                timestamp_clockout = datetime.strptime(f"{att_date} {clock_out}", "%Y-%m-%d %H:%M").strftime(
                    "%Y-%m-%d %H:%M:%S")
                payload_in = {'msnv': row['emp_code'], 'kihieumay': device_name, 'timestamp': timestamp_clockin}
                payload_out = {'msnv': row['emp_code'], 'kihieumay': device_name, 'timestamp': timestamp_clockout}

                res_in = requests.post(url, headers=headers, json=payload_in)
                res_out = requests.post(url, headers=headers, json=payload_out)
                if res_in.status_code != 200:
                    print(f"Error {res_in.status_code}: {res_in.text}")
                    break

                if res_out.status_code != 200:
                    print(f"Error {res_out.status_code}: {res_out.text}")
                    break
            except Exception as e:
                print(f"Exception on row {row['id']}: {e}")
                break

    @staticmethod
    def print_result(new_records):
        print(f"\nFound {len(new_records)} new records:")
        for i, record in enumerate(new_records, 1):
            clock_in = record.get('clock_in') or 'None'
            clock_out = record.get('clock_out') or 'None'
            print(f"{i}. {record['emp_code']} - {record['att_date']} (IN: {clock_in}, OUT: {clock_out})")


def fetch_and_process(service: TransactionService, login_by_selenium: SeleniumLogin):
    now = datetime.now()
    print(f"Running task at {now:%Y-%m-%d %H:%M:%S}")
    today = datetime.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    params = {
        "page": 1,
        "page_size": 100,
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
            "http://127.0.0.1:89/att/api/totalTimeCardReportV2/",
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
    LOGIN_URL = "http://127.0.0.1:89"
    USERNAME = "admin"
    PASSWORD = "rsC11122!"

    login = SeleniumLogin(LOGIN_URL, USERNAME, PASSWORD)
    login.login()
    time.sleep(5)
    svc = TransactionService(login.driver, LOGIN_URL)

    fetch_and_process(svc, login)
    schedule.every(5).minutes.do(fetch_and_process, svc, login)

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    finally:
        login.driver.quit()
