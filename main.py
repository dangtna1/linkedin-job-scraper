import os
import csv
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_driver(headless=False, user_data_dir=None, profile_dir=None):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")

    if user_data_dir:
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    if profile_dir:
        chrome_options.add_argument(f"--profile-directory={profile_dir}")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def scrape_linkedin_job(url, headless=False, user_data_dir=None, profile_dir=None):
    driver = get_driver(headless=headless, user_data_dir=user_data_dir, profile_dir=profile_dir)
    driver.get(url)

    data = {"url": url, "title": "", "company": "", "location": "", "posted": "", "applicants": "", "job_description": ""}

    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Scrape basic fields
        try:
            data["title"] = driver.find_element(By.CSS_SELECTOR, "h1").text
        except: pass

        try:
            data["company"] = driver.find_element(By.CSS_SELECTOR, ".topcard__org-name-link, .topcard__flavor").text
        except: pass

        try:
            data["location"] = driver.find_element(By.CSS_SELECTOR, ".topcard__flavor--bullet").text
        except: pass

        try:
            data["posted"] = driver.find_element(By.CSS_SELECTOR, ".posted-time-ago__text").text
        except: pass

        try:
            data["applicants"] = driver.find_element(By.CSS_SELECTOR, ".num-applicants__caption").text
        except: pass

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        try:
            see_more = driver.find_element(By.CSS_SELECTOR, ".show-more-less-html__button")
            driver.execute_script("arguments[0].click();", see_more)
            time.sleep(1)
        except: pass

        try:
            container = driver.find_element(By.CSS_SELECTOR, ".show-more-less-html__markup")
            data["job_description"] = driver.execute_script("return arguments[0].innerText;", container).strip()
        except: pass

    except Exception as e:
        print(f"Error scraping {url}: {e}")
    finally:
        driver.quit()

    print(f"Scraped data for {url}: {json.dumps(data, indent=2)}")
    return data


def update_csv(input_csv, headless=False, user_data_dir=None, profile_dir=None):
    # Read existing CSV
    with open(input_csv, newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys() if reader else ["url", "title", "company", "location", "posted", "applicants", "job_description"]

    # Update rows
    for row in reader:
        if row.get("url") and any(not row.get(col) for col in fieldnames if col != "url"):
            print(f"Scraping {row['url']}...")
            scraped_data = scrape_linkedin_job(
                url=row["url"],
                headless=headless,
                user_data_dir=user_data_dir,
                profile_dir=profile_dir
            )
            row.update(scraped_data)
        else:
            print(f"Skipping {row.get('url')} (already filled or no URL)")

    # Write back to CSV
    with open(input_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reader)

    print(f"CSV updated: {input_csv}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape LinkedIn jobs from a CSV")
    parser.add_argument("csv_file", help="Path to input CSV file with URLs")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode", default=True)
    parser.add_argument("--user-data-dir", help="Path to Chrome user data directory")
    parser.add_argument("--profile-dir", help="Chrome profile directory name (e.g., 'Default')")
    args = parser.parse_args()

    update_csv(
        input_csv=args.csv_file,
        headless=args.headless,
        user_data_dir=args.user_data_dir,
        profile_dir=args.profile_dir
    )
