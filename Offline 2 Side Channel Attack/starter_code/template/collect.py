import time
import json
import os
import signal
import sys
import random
import traceback
import socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import database
from database import Database

WEBSITES = [
    # websites of your choice
    "https://cse.buet.ac.bd/moodle/",
    "https://google.com",
    "https://prothomalo.com",
]

TRACES_PER_SITE = 1000
FINGERPRINTING_URL = "http://localhost:5000" 
OUTPUT_PATH = "dataset.json"

# Initialize the database to save trace data reliably
database.db = Database(WEBSITES)
database.db.init_database() 

""" Signal handler to ensure data is saved before quitting. """
def signal_handler(sig, frame):
    print("\nReceived termination signal. Exiting gracefully...")
    try:
        database.db.export_to_json(OUTPUT_PATH)
    except:
        pass
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


"""
Some helper functions to make your life easier.
"""

def is_server_running(host='127.0.0.1', port=5000):
    """Check if the Flask server is running."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def setup_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")

    # Use your manually downloaded ChromeDriver path
    service = Service(executable_path=os.path.expanduser("~/bin/chromedriver"))

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def retrieve_traces_from_backend(driver):
    """Retrieve traces from the backend API."""
    traces = driver.execute_script("""
        return fetch('/api/get_results')
            .then(response => response.ok ? response.json() : {traces: []})
            .then(data => data.traces || [])
            .catch(() => []);
    """)
    
    count = len(traces) if traces else 0
    print(f"  - Retrieved {count} traces from backend API" if count else "  - No traces found in backend storage")
    return traces or []

def clear_trace_results(driver, wait):
    """Clear all results from the backend by pressing the button."""
    clear_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Clear all results')]")
    clear_button.click()

    wait.until(EC.text_to_be_present_in_element(
        (By.XPATH, "//div[@role='alert']"), "Cleared"))
    
def is_collection_complete():
    """Check if target number of traces have been collected."""
    current_counts = database.db.get_traces_collected()
    remaining_counts = {website: max(0, TRACES_PER_SITE - count) 
                      for website, count in current_counts.items()}
    return sum(remaining_counts.values()) == 0

"""
Your implementation starts here.
"""

def collect_single_trace(driver, wait, website_url):
    """ Implement the trace collection logic here. 
    1. Open the fingerprinting website
    2. Click the button to collect trace
    3. Open the target website in a new tab
    4. Interact with the target website (scroll, click, etc.)
    5. Return to the fingerprinting tab and close the target website tab
    6. Wait for the trace to be collected
    7. Return success or failure status
    """ 

    print(f"Collecting trace for {website_url}...") 
    try: 
        driver.get(FINGERPRINTING_URL) 
        time.sleep(3) 
        try: 
            clear_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Clear all results')]")))
            clear_button.click()
        except: 
            pass 

        collect_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Collect Trace Data')]")))

        collect_button.click() 

        driver.execute_script(f"window.open('{website_url}', '_blank');") 
        driver.switch_to.window(driver.window_handles[1]) 
        time.sleep(3)  # Wait for the page to load

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Scroll to the bottom
        time.sleep(2)  # Wait for any lazy loading to complete
        driver.execute_script("window.scrollTo(0, 0);")  # Scroll back to the top 
        time.sleep(2)  # Wait for any lazy loading to complete

        driver.close()  # Close the target website tab
        driver.switch_to.window(driver.window_handles[0])  # Switch back to the fingerprinting tab

        wait.until(EC.presence_of_element_located((By.XPATH, "//h3[contains(text(),'Trace Heatmaps')]")))
        time.sleep(2)  # allow for backend save 

        traces = retrieve_traces_from_backend(driver)
        
        if not traces: 
            print("Failed to collect trace data. No traces found.") 
            return False 
        
        site_idx = database.db.get_traces_collected().get(website_url, 0)
        database.db.save_trace(website_url, site_idx, traces[-1])

        print(f"Successfully collected trace for {website_url}.") 
        return True 
    except Exception as e:
        print(f"Error collecting trace for {website_url}: {e}") 
        traceback.print_exc() 
        return False

def collect_fingerprints(driver, target_counts=None):
    """ Implement the main logic to collect fingerprints.
    1. Calculate the number of traces remaining for each website
    2. Open the fingerprinting website
    3. Collect traces for each website until the target number is reached
    4. Save the traces to the database
    5. Return the total number of new traces collected 
    """

    wait = WebDriverWait(driver, 10)
    while not is_collection_complete(): 
        for website in WEBSITES:
            current = database.db.get_traces_collected()[website] 
            if current >= TRACES_PER_SITE: 
                continue 

            success = collect_single_trace(driver, wait, website)
            if not success: 
                print(" Retrying in 5 seconds...") 
                time.sleep(5)

            time.sleep(random.uniform(1, 3))  # Random delay to avoid server overload

def main():
    """ Implement the main function to start the collection process.
    1. Check if the Flask server is running
    2. Initialize the database
    3. Set up the WebDriver
    4. Start the collection process, continuing until the target number of traces is reached
    5. Handle any exceptions and ensure the WebDriver is closed at the end
    6. Export the collected data to a JSON file
    7. Retry if the collection is not complete
    """

    print("Starting automated trace collection...") 
    if not is_server_running():
        print("Error: Flask server is not running. Please start the server first.")
        return 
    
    driver = setup_webdriver() 
    try: 
        collect_fingerprints(driver) 
    finally: 
        driver.quit()
        database.db.export_to_json(OUTPUT_PATH) 
        print("\nAll traces saved to", OUTPUT_PATH)

if __name__ == "__main__":
    main()
