import argparse
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

# PAGE_LOAD_TIMEOUT = 45


def get_driver(headless=False, user_data_dir=None, profile_dir=None):
    """Initialize Chrome WebDriver."""
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
    # driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


def scrape_linkedin_job(url, headless=False, user_data_dir=None, profile_dir=None):
    """Scrape a single LinkedIn job page."""
    driver = get_driver(headless=headless, user_data_dir=user_data_dir, profile_dir=profile_dir)
    # print("Opening Chrome... please log into LinkedIn if prompted.")
    driver.get(url)

    # Give user time to log in if needed
    # print("Waiting 45 seconds for manual login (press Enter in terminal to continue early)...")
    # try:
    #     input()
    # except EOFError:
    #     pass
    # time.sleep(3)

    data = {"url": url, "title": "", "company": "", "location": "", "posted": "", "applicants": "", "job_description": ""}

    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Scrape basic fields
        try:
            data["title"] = driver.find_element(By.CSS_SELECTOR, "h1").text
        except:
            pass

        try:
            data["company"] = driver.find_element(By.CSS_SELECTOR, ".topcard__org-name-link, .topcard__flavor").text
        except:
            pass

        try:
            data["location"] = driver.find_element(By.CSS_SELECTOR, ".topcard__flavor--bullet").text
        except:
            pass

        try:
            data["posted"] = driver.find_element(By.CSS_SELECTOR, ".posted-time-ago__text").text
        except:
            pass

        try:
            data["applicants"] = driver.find_element(By.CSS_SELECTOR, ".num-applicants__caption").text
        except:
            pass

        # Scroll to bottom to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        # Expand 'See more' if exists
        try:
            see_more = driver.find_element(By.CSS_SELECTOR, ".show-more-less-html__button")
            driver.execute_script("arguments[0].click();", see_more)
            time.sleep(1)
        except:
            pass

        # Grab full job description using innerText
        try:
            container = driver.find_element(By.CSS_SELECTOR, ".show-more-less-html__markup")
            job_desc = driver.execute_script("return arguments[0].innerText;", container)
            data["job_description"] = job_desc.strip()
        except:
            data["job_description"] = ""

    except Exception as e:
        print(f"Error while scraping: {e}")
    finally:
        driver.quit()

    print(json.dumps(data, indent=2))
    return data


def save_to_csv(data, filename):
    """Save job data to CSV."""
    fieldnames = list(data.keys())
    with open(filename if filename.endswith(".csv") else f"{filename}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(data)
    print(f"Saved CSV to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Scrape a LinkedIn job posting")
    parser.add_argument("url", help="LinkedIn job URL (must be /jobs/view/...)")
    parser.add_argument("--csv", default="output.csv", help="Output CSV filename")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode", default=True)
    parser.add_argument("--user-data-dir", help="Path to Chrome user data directory")
    parser.add_argument("--profile-dir", help="Chrome profile directory name (e.g., 'Default')")
    args = parser.parse_args()

    data = scrape_linkedin_job(
        url=args.url,
        headless=args.headless,
        user_data_dir=args.user_data_dir,
        profile_dir=args.profile_dir
    )

    save_to_csv(data, args.csv)


if __name__ == "__main__":
    main()
