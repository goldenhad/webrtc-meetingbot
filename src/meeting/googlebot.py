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

LIVESTREAM_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/google_bot_script.js"
WEBSOCKET_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/WebsocketManager.js"
TRANSCRIPT_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/google_transcripts.js"
PARTICIPANTS_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/google_participants_and_pin.js"
AUX_UTILS_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/aux_utils.js"


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


    def record_and_stream(self, duration):
        """Record the meeting for the specified duration."""
        try:
            self.driver.implicitly_wait(30) # waits 30 secs to be admitted to meeting
            self.driver.find_element(By.XPATH,"//button[@aria-label='Leave call']")

            try:
                self.driver.find_element(By.XPATH,"//span[text()='Got it']").click() # sometimes this may appear.
            except Exception as e:
                print(e)

            self.driver.implicitly_wait(10)
            self.driver.find_element(By.XPATH,'//div[@jsname="H7Z7Vb"]//button[@aria-label="More options" and @jscontroller="soHxf"]').click()

            self.driver.find_element(By.XPATH,"//span[text()='Change layout']").click()

            self.driver.find_element(By.XPATH,'//span[text()="Spotlight"]').click()

            self.driver.find_element(By.XPATH,'//button[@aria-label="Close" and @data-mdc-dialog-action="close"]').click()

            self.driver.find_element(By.XPATH,'//button[@aria-label="Show everyone"]').click()

            self.driver.find_element(By.XPATH,"//button[@aria-label='Turn on captions']").click

            # wating till this element is found before executing js
            self.driver.find_element(By.XPATH,'//div[@aria-label="Participants"]')
            self.driver.find_element(By.XPATH,"//button[@aria-label='Turn off captions']")

            # TODO: move as much UI interaction logic to python as possible.
            with open(AUX_UTILS_SCRIPT_PATH, 'r') as utils:
                with open(WEBSOCKET_SCRIPT_PATH, 'r') as ws:
                    with open(LIVESTREAM_SCRIPT_PATH, 'r') as livestream: # websocket connection is created
                        with open(PARTICIPANTS_SCRIPT_PATH, 'r') as participants: # consumes websocket connection using wsManager
                            with open(TRANSCRIPT_SCRIPT_PATH, 'r') as transcript:
                                self.driver.execute_script(f"{utils.read()} {ws.read()} {livestream.read()} {participants.read()} {transcript.read()}")
            sleep(duration)
            print("Finished recording")
        except (TimeoutException, NoSuchElementException) as e:
            print(e)

            # TODO: Add support to send the socket error
            pass

