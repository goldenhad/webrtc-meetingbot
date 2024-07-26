from pathlib import Path
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from os import environ
# from src.meeting.googlebot import LIVESTREAM_SCRIPT_PATH
from src.utils.websocketmanager import WebsocketConnection
from src.utils.constants import OUTLOOK_PWD, OUTLOOK, BOT_NAME, TEAMS_URL

LIVESTREAM_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/teams_bot_script.js"
WEBSOCKET_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/WebsocketManager.js"
AUX_UTILS_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/aux_utils.js"
PARTICIPANTS_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/teams_participants.js"
TRANSCRIPT_SCRIPT_PATH = Path(__file__).resolve().parent / "../utils/teams_transcript.js"



class TeamsMeet:
    def __init__(self, meeting_link: str, ws_url: str):
        self.mail_address: str = OUTLOOK
        self.password: str = OUTLOOK_PWD
        self.ws = WebsocketConnection(ws_url)
        self.ws.connect(self.handle_onmessage)

        # create chrome instance
        opt = Options()
        opt.add_argument('--disable-blink-features=AutomationControlled')
        opt.add_argument('--start-maximized')
        # opt.add_argument('--use-data-dir=chrome-data')
        opt.add_experimental_option(
            "prefs",
            {
                "profile.default_content_setting_values.media_stream_mic": 1,
                "profile.default_content_setting_values.media_stream_camera": 1,
                "profile.default_content_setting_values.geolocation": 0,
                "profile.default_content_setting_values.notifications": 1,
            },
        )
        self.driver: WebDriver = webdriver.Chrome(options=opt)
        self.meeting_link: str = meeting_link

    def handle_onmessage(self, message):
        """Websocket onmessage handler"""
        print(message)


    def tlogin(self):
        """
        Old login code. Unreliable. Sometimes will fail. Do not use.
        Login not required for joining meeting
        """

        # Login Page
        self.driver.get(TEAMS_URL)
        self.driver.implicitly_wait(100)
        # input outlook mail

        self.driver.find_element(By.XPATH,'//input[@type="email"]').send_keys(self.mail_address)  # enter email
        self.driver.find_element(By.XPATH,'//input[@type="submit"]').click()   # click next

        self.driver.implicitly_wait(0)  # removing implicit wait and replacing it. Should not mix implicit and explicit
        pw = WebDriverWait(self.driver,10).until(
           EC.visibility_of_element_located((By.XPATH,'//input[@type="password"]'))
        )
        pw.send_keys(self.password)
        self.driver.implicitly_wait(100)  

        self.driver.find_element(By.XPATH,'//button[text()="Sign in" and @type="submit"]').click()   # click next
        self.driver.find_element(By.ID,'acceptButton').click()  # click yes to stay signed in  


        try:
            self.driver.implicitly_wait(5)
            self.driver.find_element(By.XPATH,"//*[text()='Use the web app instead']").click()

        except:
            pass # element not found

        print("Outlook login activity: Done")


    def join_meeting(self):
        """Turns off camera and mic and joins meeting"""
        self.driver.implicitly_wait(60)
        self.driver.get(self.meeting_link)
        url = self.driver.current_url

        if "meetup-join" not in url:
            # There are 2 formats of urls. One has an iframe. Other doesn't

            # Get the iframe with id containing "experience-container"
            experience_container_iframe = self.driver.find_element(By.XPATH, '//iframe[contains(@id, "experience-container")]')

            # Switch to the iframe
            self.driver.switch_to.frame(experience_container_iframe)

        if "DEV" in environ:

            # Headless instances don't have mic and camera anyway. So don't need to worry about this
            self.driver.find_element(By.XPATH,'//div[@title="Microphone"]/div').click()
            cam = self.driver.find_element(By.XPATH,'//div[@title="Camera"]/div')
            sleep(5) # wait for camera to be available
            cam.click()

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


    def record_and_capture(self ):
        """Creates WebRTC connection and start recording the spotlighted participant"""
        try:
            self.driver.implicitly_wait(10)
            self.driver.find_element(By.ID,"view-mode-button").click()
            
            self.driver.find_element(By.XPATH,"//span[text()='Speaker']").click()


            self.driver.find_element(By.ID,"roster-button").click()

            #wait  for participants panel to show up before proceeding
            self.driver.find_element(By.XPATH,"//h2[text()='Participants' and @data-tid='right-side-panel-header-title']")

            #to switch live captions on
            actions = ActionChains(self.driver)
            actions.key_down(Keys.ALT).key_down(Keys.SHIFT).key_down("c").key_up(Keys.SHIFT).key_up(Keys.ALT).key_up("c").perform()

            with open(AUX_UTILS_SCRIPT_PATH, 'r') as utils:
                with open(WEBSOCKET_SCRIPT_PATH, 'r') as ws:
                    with open(LIVESTREAM_SCRIPT_PATH, 'r') as livestream: # websocket connection is created
                        with open(PARTICIPANTS_SCRIPT_PATH, 'r') as participants: # consumes websocket connection using wsManager
                            with open(TRANSCRIPT_SCRIPT_PATH, 'r') as transcript:
                                self.driver.execute_script(f"{utils.read()} {ws.read()} {livestream.read()} {participants.read()}")
                                self.driver.implicitly_wait(60)
                                self.driver.find_element(By.XPATH,'//div[@data-tid="closed-captions-renderer"]')
                                self.driver.execute_script(f"{transcript.read()}")
                                # self.driver.execute_script(f"{utils.read()} {ws.read()} {livestream.read()} {participants.read()} {transcript.read()}")

            sleep(600)
        except Exception as e:
            print(e)
            print("Unexpected error")




