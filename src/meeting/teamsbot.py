import sys
import json
import time
import subprocess
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Import cusrom utils
import logger
from logger import _log

# Import constants
from constants import (
    TEAMS_URL, 
    OUTLOOK_LOGIN_URL, 
    RMTP_SERVER_URL, 
    CHROME_DRIVER_PATH, 
    CONFIG_FILE_PATH, 
    TEAMS_MEETING_LINK,
    STREAM_KEY,
    INFO, 
    ERROR
)

try:
    with open(CONFIG_FILE_PATH, 'r') as f:
        config = json.load(f)
except:
    sys.exit(1)
    
def get_driver_options():
    opt = Options()
    if 'headless' in config and config['headless']:
        opt.add_argument("--headless")
        opt.add_argument("--window-size=1920,1080")
    opt.add_argument("--disable-infobars")
    opt.add_argument("--disable-popup-blocking")
    opt.add_argument("--disable-notifications")
    opt.add_argument("start-maximized")
    opt.add_argument('--no-sandbox')
    # Pass the argument 1 to allow and 2 to block
    opt.add_experimental_option("prefs", {"profile.default_content_setting_values.media_stream_mic": 1,
                                          "profile.default_content_setting_values.media_stream_camera": 1,
                                          "profile.default_content_setting_values.notifications": 2
                                          })
    return opt

browser = webdriver.Chrome(service=Service(executable_path=CHROME_DRIVER_PATH), options=get_driver_options())


sleepDelay = 20  # increase if you have a slow internet connection
timeOutDelay = 60  # increase if you have a slow internet connection

def wait_and_find_element_by_xpath(xpath, timeout=timeOutDelay):
    for i in range(timeout):
        try:
            # ele = browser.find_element_by_xpath(xpath)
            ele = browser.find_element(by=By.XPATH, value=xpath)
        except:
            sleep(3)
        else:
            return ele

def wait_and_find_ele_by_id(html_id, timeout=timeOutDelay):
    sleep(3)
    for i in range(timeout):
        print("Try Joining", html_id)
        try:
            # ele = browser.find_element_by_id(html_id)
            ele = browser.find_element(by=By.ID, value=html_id)
        except:
            sleep(3)
        else:
            return ele

def wait_and_find_ele_by_link_text(text, timeout=timeOutDelay):
    sleep(3)
    for i in range(timeout):
        try:
            # ele = browser.find_element_by_link_text(text)
            ele = browser.find_element(by=By.LINK_TEXT, value=text)
        except:
            sleep(3)
        else:
            return ele

# Record function on the browser
def record_element_asFile(id,timeout,output_filename):
    _log("Recording started...")

    ele = browser.find_element(by=By.ID, value = id)
    
    # Get element location and size
    location = ele.location
    size = ele.size

    # Define the area for ffmpeg to capture
    x = location['x']
    y = location['y']
    width = size['width']
    height = size['height']

    # Command to start ffmpeg capturing
    ffmpeg_command = [
        'ffmpeg',
        '-f', 'gdigrab',
        '-framerate', '30',  # or whatever frame rate you want
        '-video_size', f"{width}x{height}",
        '-i', f"title=Your Browser Title - Google Chrome",  # Change window title as needed
        '-offset_x', str(x),
        '-offset_y', str(y),
        '-t', '10',  # duration of recording in seconds
        '-c:v', 'libx264',  # Video codec set to H.264
        '-preset', 'fast',  # Preset for encoding speed/quality trade-off
        '-pix_fmt', 'yuv420p',  # Pixel format compatible with most browsers
        '-c:a', 'aac',  # Audio codec set to AAC
        '-b:a', '192k',  # Audio bitrate
        '-strict', '-2',  # Needed for some FFmpeg versions to enable experimental AAC encoder
        f'{output_filename}'  # Output file
    ]

    # Start recording
    subprocess.Popen(ffmpeg_command)
    # Wait for the duration of the recording
    time.sleep(10)
    _log(f"Recording finished... and save video as {output_filename}")

def record_element_rtmp_server():
    _log("Streaming started...")

    ele = browser.find_element(by=By.ID, value = id)
    
    # Get element location and size
    location = ele.location
    size = ele.size

    # Define the area for ffmpeg to capture
    x = location['x']
    y = location['y']
    width = size['width']
    height = size['height']

    ffmpeg_command = [
        'ffmpeg',
        '-f', 'gdigrab',
        '-framerate', '30',  # or whatever frame rate you want
        '-video_size', f"{width}x{height}",
        '-i', f"title=Your Browser Title - Google Chrome",  # Change window title as needed
        '-offset_x', str(x),
        '-offset_y', str(y),
        '-vcodec', 'libx264',  # Video codec set to H.264
        '-pix_fmt', 'yuv420p',  # Pixel format compatible with most browsers
        '-preset', 'veryfast',  # Faster preset for live streaming
        '-f', 'flv',  # Format for RTMP
        f'{RMTP_SERVER_URL}/{STREAM_KEY}'  # Your RTMP server URL and stream key
    ]

    # Start recording
    subprocess.Popen(ffmpeg_command)
    # Keep streaming; stop with a condition or user input
    try:
        while True:
            time.sleep(1)  # Keep the stream alive until an interrupt
    except KeyboardInterrupt:
        _log("Streaming stopped.")

    _log(f"Streaming finished ... ")

def login():
    browser.get(TEAMS_URL)  # OutLook login
    sleep(3)  # 3 sec delay
    _log("Login Teams bot and enter outlook mail")
    wait_and_find_ele_by_id('i0116').send_keys(config['outlook'])  # enter email
    wait_and_find_ele_by_id('idSIButton9').click()  # click next
    wait_and_find_ele_by_id('i0118').send_keys(config['password'])  # enter password
    wait_and_find_ele_by_id('idSIButton9').click()  # click next
    wait_and_find_ele_by_id('acceptButton').click()  # click yes to stay signed in
    web_ele = wait_and_find_ele_by_link_text('Use the web app instead', 5)
    if web_ele is not None:
        web_ele.click()


def join_meeting():
    # Open Meeting Link
    browser.get(TEAMS_MEETING_LINK)  
    _log("Started Browser")

    # Get meeting url directly
    ## Wait until the URL changes (indicating redirection)
    redirected_url = WebDriverWait(browser,3).until(
        EC.url_changes(TEAMS_MEETING_LINK)
    )
    ## Once redirected, retrieve the current URL
    final_url = browser.current_url
    _log(f"Got direct url :{final_url}")

    # Open a new tab and navigate to a new URL
    browser.execute_script("window.open('about:blank', 'new_tab')")
    new_tab_handle = browser.window_handles[-1]  # Switch to the newly opened tab
    browser.switch_to.window(new_tab_handle)
    browser.get(final_url)
    _log(f"Opened new tab")
    
    # Click join by web button
    wait_and_find_element_by_xpath('//button[@data-tid="joinOnWeb"]').click()  # join by Web

    sleep(30)    
    _log(f"Click the join on web button")
    # If the element is inside an iframe, switch to the iframe first
    try:
        iframe = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'iframe'))
        )
        browser.switch_to.frame(iframe)
        print("Switched to iframe")
    except TimeoutException:
        print("Failed to find the iframe within the given time.")

    _log(f"Enter bot username")

    # Enter username (Only working in guest Mode)
    # wait_and_find_element_by_xpath('//input[@data-tid="prejoin-display-name-input"]').send_keys(config["nickname"])  
    
    wait_and_find_ele_by_id('prejoin-join-button').click()  # join meeting

    # Wait for Main Meeting Page
    try:
        iframe = WebDriverWait(browser, 1800).until(
            EC.presence_of_element_located((By.ID, 'hangup-button'))
        )
        browser.switch_to.frame(iframe)
        print("Joined to Meeting")
    except TimeoutException:
        print("Failed to join the meeting")


    print("Joined Meeting")
    sleep(1000)

def main():
    global browser

    # browser.get("https://www.axacraft.com/")  
    # # Test recording
    # record_element_asFile("8bf49cfd-2375-8ddc-774b-668320372f59-video",10,"1.mp4")


    try:
        login()
    except:
        _log("Login Failed. Please try again.",ERROR)
        sys.exit(1)

    # Try to join meeting
    try:
        join_meeting()
    except:
        _log("Join Failed. Please try again.",ERROR)
        sys.exit(1)

    # Start recording
    try:
        record_element_asFile()
    except:
        _log("Join Failed. Please try again.",ERROR)
        sys.exit(1)

    # Attend meeting as memeber

if __name__ == "__main__":
    main()
