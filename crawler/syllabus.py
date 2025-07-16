from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import sqlite3
import traceback
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
from bs4 import BeautifulSoup

db_path = "/Users/tt1125/develop/jo-app/backend/data/lectures.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT code FROM lectures;")
codes = list(set([row[0] for row in cur.fetchall()]))  # 重複を削除

cur.close()
conn.close()

options = Options()
options.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
driver = webdriver.Chrome(options=options)

results = []

try:
    driver.set_window_size(1200, 900)
    driver.get("https://www.google.com/")
    time.sleep(1)

    # 検索ボックスを探して「佐賀大 シラバス」と入力
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys("佐賀大 シラバス")
    time.sleep(1)
    search_box.send_keys(Keys.RETURN)
    time.sleep(20)  # ロボット検証を手動で通過するための待機

    # 検索結果の一番上のリンクをクリック
    first_result = driver.find_element(By.CSS_SELECTOR, "h3")
    first_result.click()
    time.sleep(1)

    # span class="c-icon-plus"
    btn = driver.find_element(By.CSS_SELECTOR, "span.c-icon-plus")
    btn.click()
    time.sleep(1)

    for code in codes:
        # input id="subjectCode"にcodeを入力
        input_code = driver.find_element(By.ID, "subjectCode")
        input_code.clear()
        input_code.send_keys(code)
        time.sleep(1)

        wait = WebDriverWait(driver, 10)
        btn_column = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".c-btn-column-items.-x2"))
        )
        search_btn = btn_column.find_element(
            By.XPATH, ".//span[contains(@class, 'c-btn-link') and contains(., '検索')]"
        )
        wait.until(EC.element_to_be_clickable(search_btn)).click()
        time.sleep(1)

        try:
            tr = driver.find_element(By.CSS_SELECTOR, "tr.is-unread.parent.odd")
            tr.click()
            time.sleep(1)

            # ページ全体のHTMLを取得してから2つ目のc-contents-bodyを抽出
            page_html = driver.page_source
            soup = BeautifulSoup(page_html, "html.parser")
            contents_bodies = soup.find_all("div", class_="c-contents-body")
            if len(contents_bodies) >= 2:
                html = str(contents_bodies[1])  # 2個目を取得
            else:
                html = (
                    str(contents_bodies[0]) if contents_bodies else ""
                )  # 1個しかない場合は1個目
            results.append([code, html])

            # 戻る
            back_link = driver.find_element(By.CSS_SELECTOR, "a.c-page-back-link")
            back_link.click()
            time.sleep(1)
        except Exception as e:
            print(f"{code} でエラー: {e}")
            continue

    # CSVに保存
    with open("exported_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "html"])
        writer.writerows(results)

except Exception:
    error = traceback.format_exc()
    print(error)
finally:
    time.sleep(100)
    driver.quit()
