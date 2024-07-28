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
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.utils.constants import OUTLOOK_PWD, OUTLOOK, BOT_NAME, TEAMS_URL
# from src.meeting.googlebot import LIVESTREAM_SCRIPT_PATH
from src.utils.websocketmanager import WebsocketConnection

GSTREAMER_PATH = Path(__file__).resolve().parent / "../utils/webrtc_gstreamer.py"
POLL_RATE = 0.3
LIVESTREAM_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/teams_bot_script.js"
WEBSOCKET_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/WebsocketManager.js"
AUX_UTILS_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/aux_utils.js"
PARTICIPANTS_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/teams_participants.js"
TRANSCRIPT_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/teams_transcript.js"


class TeamsMeet:
    def __init__(self,
                 meeting_link,
                 xvfb_display,
                 ws_link,
                 meeting_id,
                 teams_mail=OUTLOOK,
                 teams_pw=OUTLOOK_PWD):
        self.participant_list = []
        self.mail_address = teams_mail
        self.password = teams_pw
        self.xvfb_display = xvfb_display
        self.botname = "BotAssistant"
        self.meeting_id = meeting_id
        self.meeting_link = meeting_link
        self.inference_id = uuid4()
        self.scraping_section_ids = {}
        self.websocket = WebsocketConnection(ws_link)
        self.timer = None
        self.timer_running = False

        # create chrome instance
        opt = Options()
        opt.add_argument('--disable-blink-features=AutomationControlled')
        opt.add_argument('--start-maximized')
        # opt.add_argument("--no-sandbox");
        # opt.add_argument("--disable-dev-shm-usage");
        opt.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.geolocation": 0,
            "profile.default_content_setting_values.notifications": 1
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

    def pin_participant(self, paritipant_name):
        pass

    def get_latest_transcriptions(self):
        pass

    def get_participants(self):
        attendeesParent = self.driver.find_element(By.XPATH, "//*[@aria-label='Participants']")
        attendeesContainers = attendeesParent.find_elements(By.XPATH,
                                                            ".//li[@role='presentation' and @data-cid='roster-participant']")
        participants = []
        for attendees in attendeesContainers:
            participants.append(attendees.find_element(".//span[contains(@id,'roster-avatar-img')]").text
                                )

        self.websocket.send_participants(participants)

    def tlogin(self):
        """
        Old login code. Unreliable. Sometimes will fail. Do not use.
        Login not required for joining meeting
        """

        # Login Page
        self.driver.implicitly_wait(100)
        self.driver.get(TEAMS_URL)
        self.driver.maximize_window()
        # input outlook mail

        self.driver.find_element(By.XPATH, '//input[@type="email"]').send_keys(self.mail_address)  # enter email
        self.driver.find_element(By.XPATH, '//input[@type="submit"]').click()  # click next

        self.driver.implicitly_wait(0)  # removing implicit wait and replacing it. Should not mix implicit and explicit
        pw = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//input[@type="password"]'))
        )
        pw.send_keys(self.password)
        self.driver.implicitly_wait(100)

        self.driver.find_element(By.XPATH, '//button[text()="Sign in" and @type="submit"]').click()  # click next
        self.driver.find_element(By.ID, 'acceptButton').click()  # click yes to stay signed in  

        try:
            self.driver.implicitly_wait(5)
            self.driver.find_element(By.XPATH, "//*[text()='Use the web app instead']").click()

        except:
            pass  # element not found

        print("Outlook login activity: Done")

    def join_meeting(self):
        """Turns off camera and mic and joins meeting"""
        self.driver.implicitly_wait(60)
        self.driver.get(self.meeting_link)
        self.driver.maximize_window()
        url = self.driver.current_url

        if "meetup-join" not in url:
            # There are 2 formats of urls. One has an iframe. Other doesn't

            # Get the iframe with id containing "experience-container"
            experience_container_iframe = self.driver.find_element(By.XPATH,
                                                                   '//iframe[contains(@id, "experience-container")]')

            # Switch to the iframe
            self.driver.switch_to.frame(experience_container_iframe)

        if "DEV" in environ:
            pass
            # Headless instances don't have mic and camera anyway. So don't need to worry about this
            # self.driver.find_element(By.XPATH,'//div[@title="Microphone"]/div').click()
            # cam = self.driver.find_element(By.XPATH,'//div[@title="Camera"]/div')
            # sleep(5) # wait for camera to be available
            # cam.click()

        # Get the button with id "prejoin-join-button"
        input_element = self.driver.find_element(By.XPATH, '//input[@type="text"][@placeholder="Type your name"]')

        # Click the input element
        input_element.click()
        input_element.send_keys(BOT_NAME)

        self.driver.implicitly_wait(10)
        self.driver.find_element(By.ID, 'prejoin-join-button').click()

        # Click the join button
        # Wait for Main Meeting Page
        try:
            WebDriverWait(self.driver, 1800).until(
                EC.presence_of_element_located((By.ID, 'hangup-button'))
            )
            print("Joined Meeting")
        except TimeoutException:
            print("Failed to join the meeting")

    def record_and_stream(self):
        """Creates WebRTC connection and start recording the spotlighted participant"""
        try:
            self.driver.implicitly_wait(30)
            self.driver.find_element(By.ID, "view-mode-button").click()

            self.driver.find_element(By.XPATH, "//span[text()='Speaker']").click()

            self.driver.find_element(By.ID, "roster-button").click()

            # wait  for participants panel to show up before proceeding
            self.driver.find_element(By.XPATH,
                                     "//h2[text()='Participants' and @data-tid='right-side-panel-header-title']")

            # to switch live captions on
            actions = ActionChains(self.driver)
            actions.key_down(Keys.ALT).key_down(Keys.SHIFT).key_down("c").key_up(Keys.SHIFT).key_up(Keys.ALT).key_up(
                "c").perform()

            video_element = self.driver.find_element(By.XPATH,
                                                     "//*[@data-tid='SpeakerStage-wrapper']//*[@data-cid='calling-participant-stream']")

            panel_height = self.driver.execute_script('return window.outerHeight - window.innerHeight;')
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
        except Exception as e:
            print(e)
            print("Unexpected error")


if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        teams = TeamsMeet(args[0],  # meeting url
                          args[1],  # xvfb numner 
                          args[2],  # ws_link 
                          args[3],  # meeting_id
                          )
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
        asyncio.get_event_loop().run_until_complete(teams.websocket.connect())
        teams.join_meeting()
        teams.record_and_stream()
        while True:
            teams.get_latest_transcriptions()
            teams.get_participants()
            sleep(POLL_RATE)

    except Exception as e:
        raise e
