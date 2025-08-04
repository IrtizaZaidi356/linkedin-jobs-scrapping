import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def extract_job_details(driver, job_url):
    driver.get(job_url)
    time.sleep(2)

    try:
        title = driver.find_element(By.CSS_SELECTOR, "h1.top-card-layout__title").text.strip()
    except:
        title = "N/A"

    try:
        company = driver.find_element(By.CSS_SELECTOR, "a.topcard__org-name-link").text.strip()
    except:
        try:
            company = driver.find_element(By.CSS_SELECTOR, "span.topcard__flavor").text.strip()
        except:
            company = "N/A"

    return title, company


def get_jobs(job_title, city, country, no_of_jobs):
    job_list = []

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("window-size=1920,1080")

    driver = webdriver.Chrome(options=options)

    search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title}&location={city},%20{country}"
    driver.get(search_url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list"))
        )
    except:
        st.error("❌ Job list did not load.")
        driver.quit()
        return pd.DataFrame()

    job_links = []
    jobs = driver.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list li a")
    for job in jobs:
        link = job.get_attribute("href")
        if link and '/jobs/view/' in link:
            job_links.append(link)
        if len(job_links) >= no_of_jobs:
            break

    for idx, link in enumerate(job_links):
        title, company = extract_job_details(driver, link)
        job_list.append({
            "S.No": idx + 1,
            "Title": title,
            "Company": company,
            "Location": f"{city} | {country}",
            "Link": link
        })

    driver.quit()
    return pd.DataFrame(job_list)


# ──────────────────────────── Streamlit App ────────────────────────────
st.set_page_config(page_title="🌍 Global LinkedIn Job Scraper", layout="centered")
st.title("🌍 LinkedIn Job Scraper")

with st.form("job_form"):
    job_title = st.text_input(
        "Job Title",
        value="",
        placeholder="e.g. Software Engineer, Data Analyst"
    )
    city = st.text_input(
        "City",
        value="",
        placeholder="e.g. Dubai, Karachi, London"
    )
    country = st.text_input(
        "Country",
        value="",
        placeholder="e.g. Pakistan, UAE, UK"
    )
    no_of_jobs = st.slider("Number of Jobs", 1, 30, 5)

    submitted = st.form_submit_button("Scrape Jobs")

# On submit
if submitted:
    if not job_title.strip() or not city.strip() or not country.strip():
        st.warning("⚠️ Please enter a valid Job Title, City, and Country.")
    else:
        with st.spinner("🔍 Scraping jobs..."):
            df = get_jobs(job_title, city, country, no_of_jobs)

            if df.empty:
                st.warning("⚠️ No jobs found or LinkedIn layout changed.")
            else:
                st.success(f"✅ Scraped {len(df)} job(s)")
                st.dataframe(df)

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv,
                    file_name=f"{job_title}_{city}_{country}_jobs.csv",
                    mime="text/csv"
                )
