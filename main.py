import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Initialize Streamlit app
st.title("Instagram Follower Scraper")
st.markdown("A simple web scraper to fetch followers from an Instagram account.")

# User inputs for Instagram login credentials and target account
username = st.text_input("Enter your Instagram Username", value="amateurs_can_fucking_suck_it")
password = st.text_input("Enter your Instagram Password", type="password", value="manvith@2725")
target_account = st.text_input("Enter Target Instagram Account", value="manhdi_manchan")

# Button to trigger the scraping process
if st.button("Scrape Followers"):
    
    # Initialize the browser with Chrome options
    st.info("Setting up the browser...")
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Headless mode, no UI
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    def login_instagram():
        driver.get("https://www.instagram.com/accounts/login/")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, 'username')))
        
        # Enter username
        username_input = driver.find_element(By.NAME, 'username')
        username_input.send_keys(username)

        # Enter password
        password_input = driver.find_element(By.NAME, 'password')
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
        WebDriverWait(driver, 20).until(EC.url_changes("https://www.instagram.com/accounts/login/"))

    def navigate_to_followers():
        # Navigate to target account
        driver.get(f"https://www.instagram.com/{target_account}/")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'/followers/')]")))
        
        # Wait for the followers button to be present and clickable
        wait = WebDriverWait(driver, 20)
        followers_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'/followers/')]")))
        followers_link.click()
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']")))

    def scrape_followers():
        try:
            followers_popup = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//ul"))
            )
            last_height = driver.execute_script("return arguments[0].scrollHeight", followers_popup)
            
            followers = []
            while True:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", followers_popup)
                time.sleep(2)
                new_height = driver.execute_script("return arguments[0].scrollHeight", followers_popup)

                # Scrape follower usernames using the updated class name
                follower_elements = followers_popup.find_elements(By.CLASS_NAME, '_ap3a _aaco _aacw _aacx _aad7 _aade')
                for elem in follower_elements:
                    try:
                        username = elem.find_element(By.CSS_SELECTOR, 'a').get_attribute('href').split("/")[-2]
                        if username not in followers:
                            followers.append(username)
                    except Exception as e:
                        st.error(f"Error extracting username: {e}")

                # Break the loop when no more scrolling happens
                if new_height == last_height:
                    break
                last_height = new_height
            
            return followers
        except Exception as e:
            st.error(f"Error scraping followers: {e}")
            return []

    # Try block to handle potential errors
    try:
        st.info("Logging in to Instagram...")
        login_instagram()
        st.success("Logged in successfully!")

        st.info(f"Navigating to {target_account}'s followers...")
        navigate_to_followers()
        
        st.info("Scraping followers...")
        followers_list = scrape_followers()

        st.success(f"Scraped {len(followers_list)} followers.")
        st.write(followers_list)
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        driver.quit()
