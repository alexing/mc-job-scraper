import requests
import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


def shorten_url(long_url):
    api_url = f"http://tinyurl.com/api-create.php?url={long_url}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error shortening URL: {response.status_code}, {response.text}")
        return long_url


def scrape_jobs(url, chrome_path):
    jobs = []

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-gpu")  # Disable GPU acceleration
    options.add_argument("--window-size=1920,1080")  # Set window size

    # Make sure to set the correct path for the Chrome binary
    options.binary_location = chrome_path

    driver = webdriver.Chrome(options=options)

    driver.get(url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-list-item")))

    page = 0
    while True:
        page += 1
        job_listings = driver.find_elements(By.CLASS_NAME, "jobs-list-item")
        print(f"Found {len(job_listings)} job listings on page {page}.")

        if not job_listings:
            break

        for job in job_listings:
            try:
                title_element = job.find_element(By.CSS_SELECTOR, "a[data-ph-at-id='job-link']")
                title = title_element.find_element(By.CLASS_NAME, "job-title").text
                link = title_element.get_attribute("href")
                location_element = job.find_element(By.CSS_SELECTOR, "span.job-location")
                location = location_element.text
                jobs.append({'title': title, 'link': link, 'location': location})
            except Exception as e:
                print(f"Error extracting job details: {e}")
                continue

        try:
            # Handle overlay if present
            try:
                overlay = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.onetrust-pc-dark-filter")))
                driver.execute_script("arguments[0].style.visibility='hidden'", overlay)
            except:
                pass

            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-ph-at-id='pagination-next-link']")))
            next_button.click()
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-list-item")))
        except Exception as e:
            print(f"Error advancing to next page, breaking: {e}")
            break

    driver.quit()
    return jobs


def filter_jobs_by_location(jobs, location):
    return [job for job in jobs if location.lower() in job['location'].lower()]


if __name__ == "__main__":
    config = load_config('config.yaml')
    chrome_path = config['chrome_path']
    keywords = config['keywords']
    location = config['location']
    url = f'https://careers.mastercard.com/us/en/search-results?keywords={keywords}'
    jobs = scrape_jobs(url, chrome_path)
    filtered_jobs = filter_jobs_by_location(jobs, location)

    for job in filtered_jobs:
        short_url = shorten_url(job['link'])
        print(f"{job['title']}: {short_url}")
