# Get data after 5 minutes

## 📋 System Requirements

- Python 3.10 or higher
- Google Chrome installed
- Chrome WebDriver compatible with your Chrome version

---

## ⚙️ Installation

### 1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows
```

## 2. Install dependencies:

```bash
pip install -r requirements
```

## 3. Install Chrome WebDriver:

- 🔧 On Linux:

```bash
    sudo apt update
    sudo apt install chromium-chromedriver
  ```

- 🍎 On macOS (with Homebrew):
    ```
    brew install chromedriver
    ```
    - 👉 https://sites.google.com/chromium.org/driver/
    - After downloading, extract it and either:
        - Place the binary in a directory in your system PATH, or
        - Provide the full path in your Python script (e.g.,/usr/bin/chromedriver)
- 🖥️ On Windows:
    - Download the [ChromeDriver](https://chromedriver.chromium.org/downloads) executable.
    - Extract the downloaded file and place the `chromedriver.exe` in a directory that's in your system's PATH.

## 🚀 Usage

1. Start the server:

```bash
python main.py
```
2. Build library:
```bash
pip install pyinstaller
pyinstaller --onefile --icon="C:path\icon" "main.py"
```
