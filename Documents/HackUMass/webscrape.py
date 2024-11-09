from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Specify the path to your ChromeDriver for macOS
service = Service("/Users/novaxion/Desktop/chromedriver-mac-x64/chromedriver")


driver = webdriver.Chrome(service=service, options=options)

url = "https://www.formula1.com/en/results.html"
driver.get(url)
time.sleep(2)

race_data = []

try:
    races = driver.find_elements(By.CSS_SELECTOR, ".race-entry")
    for race in races:
        race_name = race.find_element(By.CSS_SELECTOR, ".race-name").text
        year = 2024

        race_url = race.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
        driver.get(race_url)
        time.sleep(2)

        lap_times = []
        lap_table = driver.find_element(By.CSS_SELECTOR, ".lap-time-table")
        rows = lap_table.find_elements(By.TAG_NAME, "tr")

        for lap_no, row in enumerate(rows, start=1):
            columns = row.find_elements(By.TAG_NAME, "td")
            if columns:
                driver_name = columns[0].text
                lap_time = columns[1].text
                lap_times.append({
                    "driver_name": driver_name,
                    "lap_no": lap_no,
                    "lap_time": lap_time
                })

        race_data.append({
            "race_name": race_name,
            "year": year,
            "lap_times": lap_times
        })

        driver.get(url)
        time.sleep(2)
except Exception as e:
    print("An error occurred during scraping:", e)

driver.quit()

for race in race_data:
    print(f"Race: {race['race_name']} ({race['year']})")
    for lap in race['lap_times']:
        print(f"Driver: {lap['driver_name']}, Lap: {lap['lap_no']}, Time: {lap['lap_time']}")
