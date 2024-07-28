import asyncio
import json
import subprocess
import sys
import threading
from os import environ
from pathlib import Path
from time import sleep
from uuid import uuid4

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from src.utils.constants import GMAIL, GMAIL_PWD
from src.utils.websocketmanager import WebsocketConnection

GSTREAMER_PATH = Path(__file__).resolve().parent / "../utils/webrtc_gstreamer.py"
POLL_RATE = 0.2
LIVESTREAM_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/google_bot_script.js"
WEBSOCKET_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/WebsocketManager.js"
TRANSCRIPT_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/google_transcripts.js"
PARTICIPANTS_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/google_participants_and_pin.js"
AUX_UTILS_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/aux_utils.js"


class GoogleMeet:
    def __init__(self, meeting_link, xvfb_display, ws_link, meeting_id):
        self.mail_address = GMAIL
        self.password = GMAIL_PWD
        self.meeting_link = meeting_link
        self.participant_list = []
        self.inference_id = uuid4()
        self.scraping_secion_ids = {}
        self.websocket = WebsocketConnection(ws_link)
        self.participant_list = []
        self.xvfb_display = xvfb_display
        self.meeting_id = meeting_id
        self.timer = None
        self.timer_running = False
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

    def start_timer(self, interval, func):
        # Cancel any existing timer before starting a new one
        if self.timer_running:
            self.cancel_timer()

        print("Starting timer...")
        self.timer = threading.Timer(interval, func)
        self.timer.start()
        self.timer_running = True

    def cancel_timer(self):
        if self.timer is not None:
            print("Cancelling timer...")
            self.timer.cancel()
            self.timer_running = False

    def is_timer_running(self):
        return self.timer_running

    async def loop(self):
        message = await self.websocket.conn.recv()
        msg: dict = json.loads(message)
        print(msg)
        event = msg["event"]

        if event == "select-subject":
            print("need to call pin participant")
            self.pin_participant(msg['data'])
            print("finished pin participant func")
        return 0

    def exit_func(self):

        self.driver.quit()
        print("should quit")

    def pin_participant(self, participant_name):
        participants = self.driver.find_elements(By.XPATH, '//div[@aria-label="Participants"]//span[@class="zWGUib"]')
        for participant in participants:
            pin_icon = participant.find_elements(By.XPATH,
                                                 './/i[text()="keep"]',
                                                 )
            if pin_icon:
                if participant.find_element(By.XPATH, ".//span[@class='zWGUib']").text != participant_name:
                    participant.find_element(By.XPATH, "//button[@aria-label='More actions']").click()
                    self.driver.find_element(By.XPATH, "//span[text()='Unpin']").click()
            else:
                if participant.find_element(By.XPATH, ".//span[@class='zWGUib']").text == participant_name:
                    participant.find_element(By.XPATH, "//button[@aria-label='More actions']").click()
                    self.driver.find_element(By.XPATH, "//span[text()='Pin to screen']").click()
                    self.driver.find_element(By.XPATH, "//*[text()='For myself only']").click()
        print("pinned participant")

    def get_latest_transcription(self):
        pass

    def get_participants(self):
        spans = self.driver.find_elements(By.XPATH, '//div[@aria-label="Participants"]//span[@class="zWGUib"]')
        for span in spans:
            if span.text not in self.participant_list:
                self.participant_list.append(span.text)

        if len(self.participant_list) < 3:
            if not self.is_timer_running():
                self.start_timer(30, self.exit_func)
        elif self.is_timer_running():
            self.cancel_timer()

    def glogin(self):

        """Login to Gmail."""
        self.driver.get(
            'https://accounts.google.com/ServiceLogin?hl=en&passive=true&continue=https://www.google.com/&ec=GAZAAQ')

        self.driver.maximize_window()
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
            self.driver.implicitly_wait(60)  # waits 60 secs to be admitted to meeting
            self.driver.find_element(By.XPATH, "//button[@aria-label='Leave call']")

            self.driver.implicitly_wait(10)
            try:
                self.driver.find_element(By.XPATH, "//span[text()='Got it']").click()  # sometimes this may appear.
            except Exception as e:
                print(e)

            self.driver.implicitly_wait(20)
            self.driver.find_element(By.XPATH,
                                     '//div[@jsname="H7Z7Vb"]//button[@aria-label="More options" and @jscontroller="soHxf"]').click()

            self.driver.implicitly_wait(10)
            self.driver.find_element(By.XPATH, "//span[text()='Change layout']").click()

            self.driver.find_element(By.XPATH, '//span[text()="Spotlight"]').click()

            self.driver.find_element(By.XPATH,
                                     '//button[@aria-label="Close" and @data-mdc-dialog-action="close"]').click()

            # minimising self video element
            self_vid = self.driver.find_element(
                By.XPATH, "//*[@class='aGWPv']"  # self video element
            )
            print("got self video element")
            ActionChains(self.driver).move_to_element_with_offset(self_vid, 20, 20).perform()
            self_vid.find_element(By.XPATH, "//*[@aria-label='More options']").click()
            print("moved to my vid and clicked")
            sleep(5)
            print("clicked more options")
            self.driver.find_element(By.XPATH, "//*[text()='Minimize']").click()
            print("clicked minimise")

            self.driver.find_element(By.XPATH, '//button[@aria-label="Show everyone"]').click()

            self.driver.find_element(By.XPATH, "//button[@aria-label='Turn on captions']").click()

            # wating till this element is found before executing js
            self.driver.find_element(By.XPATH, '//div[@aria-label="Participants"]')
            self.driver.find_element(By.XPATH, "//button[@aria-label='Turn off captions']")

            panel_height = self.driver.execute_script('return window.outerHeight - window.innerHeight;')

            video_element = self.driver.find_element(By.XPATH, "//*[@class='oZRSLe']")

            if video_element:
                print("got video element")
                height, width, x, y = video_element.rect.values()
                y += panel_height
                self.height = height
                self.width = width
                self.x = x
                self.y = y
                print("got coords")

                self.websocket.send_analysing(
                    self.meeting_id,
                    self.inference_id
                )
                print("send analysing")
                # sleep(duration)

                subprocess.Popen([
                    # "xvfb-run --listen-tcp --server-num=44 --auth-file=/tmp/xvfb.auth -s "-ac -screen 0 1920x1080x24" /
                    "python",
                    str(GSTREAMER_PATH.resolve()),
                    "--display_num",
                    f":{self.xvfb_display}",
                    "--startx",
                    str(int(x)),
                    "--starty",
                    str(int(y)),
                    "--endx",
                    str(int(x + width)),
                    "--endy",
                    str((y + height))
                ])
                print("opened gstreamer process")

            print("Started streaming")
        except (TimeoutException, NoSuchElementException) as e:
            print(e)

            # TODO: Add support to send the socket error
            pass


if __name__ == "__main__":

    args = sys.argv[1:]
    google = GoogleMeet(
        # "https://meet.google.com/zjv-imfz-rty",
        # "ws://localhost:7000"
        args[0],  # meeting url
        args[1],  # xvfb numner 
        args[2],  # ws_link 
        args[3],  # meeting_id
    )
    print(args)
    try:

        # subprocess.Popen([
        #     # "xvfb-run --listen-tcp --server-num=44 --auth-file=/tmp/xvfb.auth -s "-ac -screen 0 1920x1080x24" /
        #     "python",
        #     str(GSTREAMER_PATH.resolve()),
        #     "--display_num",
        #     f":{args[1]}",
        #     "--startx",
        #     "0",
        #     "--starty",
        #     "0",
        #     "--endx",
        #     "1920",
        #     "--endy",
        #     "1080",
        # ])
        asyncio.get_event_loop().run_until_complete(google.websocket.connect())
        google.glogin()
        sleep(10)  # need to wait for google account to figure itself out
        google.join_meeting()
        google.record_and_stream(300)
        print("finished runjning google websocket connect")

    except Exception as e:
        print(e)
        google.driver.save_screenshot("failed.png")
    while True:
        google.get_participants()
        google.get_latest_transcription()
