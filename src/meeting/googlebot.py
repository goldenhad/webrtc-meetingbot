from os import environ
from time import sleep
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.utils.constants import GMAIL, GMAIL_PWD
from src.utils.websocketmanager import WebsocketConnection

SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/google_bot_script.js"


class GoogleMeet:
    def __init__(self, meeting_link: str, ws_url: str):
        self.mail_address = GMAIL
        self.password = GMAIL_PWD
        self.meeting_link = meeting_link
        self.ws = WebsocketConnection(ws_url)
        self.ws.connect(self.handle_onmessage)
        # Create Chrome instance
        opt = Options()
        opt.add_argument('--disable-blink-features=AutomationControlled')
        opt.add_argument('--start-maximized')
        opt.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.geolocation": 0,
            "profile.default_content_setting_values.notifications": 1
        })
        self.driver = webdriver.Chrome(options=opt)

    def handle_onmessage(self,message):
        """Websocket onmessage handler""" 
        print(message)

    def glogin(self):

        """Login to Gmail."""
        self.driver.get('https://accounts.google.com/ServiceLogin?hl=en&passive=true&continue=https://www.google.com/&ec=GAZAAQ')

        # Input Gmail
        self.driver.find_element(By.ID, "identifierId").send_keys(self.mail_address)
        self.driver.find_element(By.ID, "identifierNext").click()
        self.driver.implicitly_wait(10)

        # Input Password
        self.driver.find_element(By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input').send_keys(self.password)
        self.driver.implicitly_wait(10)
        self.driver.find_element(By.ID, "passwordNext").click()
        self.driver.implicitly_wait(10)

        # Go to Google home page
        self.driver.get('https://google.com/')
        self.driver.implicitly_wait(100)
        print("Gmail login activity: Done")

    def join_meeting(self):
        """Turn off microphone and camera in Google Meet."""
        self.driver.get(self.meeting_link)
        self.driver.implicitly_wait(20)


        if "DEV" in environ:

            # Turn off Microphone
            self.driver.find_element(By.CSS_SELECTOR, 'div[jscontroller="t2mBxb"][data-anchor-id="hw0c9"]').click()
            self.driver.implicitly_wait(3000)
            print("Turn off mic activity: Done")

            # Turn off Camera
            sleep(1)
            self.driver.find_element(By.CSS_SELECTOR, 'div[jscontroller="bwqwSd"][data-anchor-id="psRWwc"]').click()
            self.driver.implicitly_wait(3000)
            print("Turn off camera activity: Done")

            self.driver.implicitly_wait(2000)
            self.driver.find_element(By.CSS_SELECTOR, 'button[jsname="Qx7uuf"]').click()
            print("Ask to join activity: Done")

            try:
                print("Check if join try")
                self.driver.implicitly_wait(10)
                self.driver.find_element(By.TAG_NAME, 'video')
                print("Meeting has been joined")
            except (TimeoutException, NoSuchElementException):
                print("Meeting has not been joined")

    def record_and_stream(self, duration):
        """Record the meeting for the specified duration."""
        try:
            sleep(10)
            self.driver.implicitly_wait(60)
            spotlighted_video_elements = self.driver.find_elements(By.XPATH, '//ancestor::div[@data-participant-id]' + 
                     '//span[@aria-label="Pinned for everyone"]/preceding::video[1]')

            with open(SCRIPT_PATH, 'r') as file:
                # Only the first spotlighted element is going to be shown
                self.driver.execute_script(file.read(), spotlighted_video_elements[0])
                sleep(duration)
            print("Finished recording")
        except (TimeoutException, NoSuchElementException):
            # TODO: Add support to send the socket error
            pass

