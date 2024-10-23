import datetime
import subprocess
import sys
import threading
from os import environ
from pathlib import Path
from time import sleep, time
import difflib

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from src.meeting.botbase import BotBase
from src.utils.constants import GMAIL, GMAIL_PWD, BOT_NAME

GSTREAMER_PATH = Path(__file__).resolve().parent / "../utils/webrtc_gstreamer.py"
POLL_RATE = 0.2


class GoogleMeet(BotBase):
    def __init__(self, meeting_link, xvfb_display, ws_link, meeting_id):
        self.content = ""
        self.last_sent = datetime.datetime.now()
        self.mail_address = GMAIL
        self.password = GMAIL_PWD
        self.meeting_link = meeting_link
        self.scraping_section_ids = {}
        self.prev_subject = ""
        self.last_subject_sent_time = time()
        super().__init__(ws_link, xvfb_display, meeting_id)

    def pin_participant(self, participant_name):
        participants = self.driver.find_elements(By.XPATH, '//div[@aria-label="Participants"]//div[@role="listitem"]')
        for participant in participants:
            self.driver.implicitly_wait(1)
            pin_icon = participant.find_elements(By.XPATH,
                                                 './/i[text()="keep"]',
                                                 )
            name = participant.find_element(By.XPATH, ".//span[@class='zWGUib']").text
            if pin_icon:
                if name != participant_name:
                    participant.find_element(By.XPATH, ".//button[@aria-label='More actions']").click()
                    self.driver.implicitly_wait(5)
                    sleep(1)
                    self.driver.find_element(By.XPATH, "//span[text()='Unpin']").click()
            else:
                if name == participant_name:
                    participant.find_element(By.XPATH, ".//button[@aria-label='More actions']").click()
                    self.driver.implicitly_wait(5)
                    sleep(1)
                    self.driver.find_element(By.XPATH, "//span[text()='Pin to screen']").click()
        print("pinned participant")
        self.driver.implicitly_wait(10)

    def get_latest_transcription(self):
        self.driver.implicitly_wait(1)
        transcription_holder = self.driver.find_elements(By.XPATH, '//div[@class="iOzk7"]')
        target_element = None
        for element in transcription_holder:
            if element.value_of_css_property('display') != 'none':
                target_element = element
                break
        if target_element is not None:
            try:
                transcription_sections = target_element.find_elements(By.XPATH, "./div")
                content = ""
                if len(transcription_sections) > 0:
                    section = transcription_sections[-1]
                    spans = section.find_elements(By.XPATH, ".//span")
                    author = section.find_element(By.XPATH, "./div[1]/div").text
                    print("author " + author)
                    for span in spans:
                        print(span.text)
                        content += span.text.strip() + " "

                    print("content " + content)
                    if self.content != content:
                        diff = difflib.ndiff(content, self.content)
                        diff_list = [char for char in diff if char.startswith('- ')]
                        diff_text =  ''.join(char[2:] for char in diff_list)
                        self.websocket.send_transcription(
                            author,
                            diff_text.strip(),
                            datetime.datetime.now(),
                            self.last_sent,

                        )
                        self.last_sent = datetime.datetime.now()
                        self.content = content
            except Exception as e:  # sometimes staleelement errors are thrown
                print(e)

    def get_participants(self):
        try:
            new_list = []
            spans = self.driver.find_elements(By.XPATH, '//div[@aria-label="Participants"]//span[@class="zWGUib"]')
            for span in spans:
                new_list.append(span.text)

            if len(self.participant_list) < 3:
                if not self.is_timer_running():
                    self.start_timer(6000, self.exit_func)
            elif self.is_timer_running():
                self.cancel_timer()

            if new_list != self.participant_list:
                print(new_list)
                self.websocket.send_participants(
                    new_list
                )
            self.participant_list = new_list

            subject = self.driver.find_element(By.XPATH,"//*[@class='oZRSLe']//div[@class='dwSJ2e']").text
            current_time = time()
            elapsed_time = current_time - self.last_subject_sent_time 
            if elapsed_time > 1:
                self.websocket.send_subject(subject)
                self.prev_subject = subject
                self.last_subject_sent_time = current_time
        except Exception as e:
            print("had a problem with getting participants")
            print(e)
            # Might give a stale element reference when the person in question has left
    def glogin(self):
        """Login to Gmail."""
        self.driver.get(
            'https://accounts.google.com/ServiceLogin?hl=en&passive=true&continue=https://www.google.com/&ec=GAZAAQ')

        self.driver.implicitly_wait(10)
        self.driver.maximize_window()
        # Input Gmail
        self.driver.find_element(By.ID, "identifierId").send_keys(self.mail_address)
        self.driver.find_element(By.ID, "identifierNext").click()

        # Input Password
        self.driver.find_element(By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input').send_keys(self.password)
        self.driver.find_element(By.ID, "passwordNext").click()

        # Go to Google home page
        self.driver.get('https://google.com/')
        self.driver.implicitly_wait(100)
        print("Gmail login activity: Done")

    def join_meeting(self):
        """Turn off microphone and camera in Google Meet."""
        self.driver.get(self.meeting_link)
        self.driver.implicitly_wait(20)

        # Turn off Microphone
        self.driver.find_element(By.XPATH, '//*[@aria-label="Turn off microphone"]').click()
        self.driver.implicitly_wait(3000)
        print("Turn off mic activity: Done")

        # Turn off Camera
        sleep(1)
        self.driver.find_element(By.XPATH, '//*[@aria-label="Turn off camera"]').click()
        self.driver.implicitly_wait(3000)
        print("Turn off camera activity: Done")

        try:
            self.driver.find_element(By.XPATH,"//input[@aria-label='Your name']").send_keys(BOT_NAME)
            self.driver.implicitly_wait(2000)
            self.driver.find_element(By.XPATH,"//span[text()='Ask to join']").click()
            print("Ask to join activity: Done")
        except:
            print("had an error")
            self.driver.save_screenshot("error.png")

    def record_and_stream(self):
        """Record the meeting for the specified duration."""
        self.driver.implicitly_wait(60)  # waits 60 secs to be admitted to meeting
        self.driver.find_element(By.XPATH, "//button[@aria-label='Leave call']")

        # self.driver.implicitly_wait(30)
        # self.driver.find_element(By.XPATH,"//*[text()='Got it']").click()
        # print("clicked got it")

        try:
            self.driver.implicitly_wait(10)
            self.driver.find_element(By.XPATH,
                                     '//div[@jsname="H7Z7Vb"]//button[@aria-label="More options"]').click()
            print("clicked more options")
        except:
            print("failed clicking more options") 

        self.driver.implicitly_wait(10)
        self.driver.find_element(By.XPATH, "//li[.//span[text()='Change layout']]").click()

        self.driver.find_element(By.XPATH, '//span[text()="Spotlight"]').click()

        self.driver.find_element(By.XPATH,
                                 '//button[@aria-label="Close" and @data-mdc-dialog-action="close"]').click()

        # minimising self video element
        self_vid = self.driver.find_element(
            By.XPATH, "//div[contains(@class, 'aGWPv') and .//div[contains(@class,'dwSJ2e') and contains(text(), 'AssistantBot')]]"  # self video element
        )
        print("got self video element")

        WebDriverWait(self.driver,30).until(
            expected_conditions.invisibility_of_element((By.XPATH,"//*[contains(data-key,'notification')]"))
        )
        print("notification is gone now")

        ActionChains(self.driver).move_to_element_with_offset(self_vid, 30, 30).click().perform()

        print("moved to my vid and clicked")

        self_vid.find_element(By.XPATH, ".//*[@aria-label='More options']").click()
        print("clicked more options")
        self.driver.find_element(By.XPATH, "//*[text()='Minimize']").click()
        print("clicked minimise")

        self.driver.find_element(By.XPATH, '//button[@aria-label="Show everyone"]').click()

        self.driver.find_element(By.XPATH, "//button[@aria-label='Turn on captions']").click()

        # wating till this element is found before executing js
        self.driver.find_element(By.XPATH, '//div[@aria-label="Participants"]')
        self.driver.find_element(By.XPATH, "//button[@aria-label='Turn off captions']")

        sleep(5)  # to make sure captions area is initialised
        panel_height = self.driver.execute_script('return window.outerHeight - window.innerHeight;')

        self.driver.implicitly_wait(60)
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

            self.gstreamer_process = subprocess.Popen([
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
                str((y + height)),
                '--meetingId',
                self.meeting_id
            ])
            print("opened gstreamer process")

        print("Started streaming")

    def unpin_all(self):
        # Only 1 participant is pinned at any time. So this works
        try:
            self.driver.implicitly_wait(3)
            video_element = self.driver.find_element(By.XPATH, "//*[@class='oZRSLe']") # the main video element. 
            print("got main vid elementj")
            ActionChains(self.driver).move_to_element_with_offset(video_element,30,30).click().perform()
            print("clicked main vid element")

            self.driver.implicitly_wait(0)
            WebDriverWait(self.driver,10).until(
                expected_conditions.element_to_be_clickable((By.XPATH,"//*[@class='oZRSLe']//button[@aria-label='Unpin']"))
            ).click()
            print("clicked unpin")
            self.driver.implicitly_wait(10)
        except Exception as e:
            print("Unpin was called. But most likely no one is pinned!:",e)
    
    def check_meeting_ended(self):
        try:
            self.driver.find_element(By.XPATH, "//button[@aria-label='Leave call']")
        except:
            # No leave call button found. Exit
            print("meeting ended. should quit")
            self.exit_func()

if __name__ == "__main__":
    google = None
    try:
        args = sys.argv[1:]
        print(args)
        google = GoogleMeet(
            # "https://meet.google.com/zjv-imfz-rty",
            # "ws://localhost:7000"
            args[0],  # meeting url
            args[1],  # xvfb numner 
            args[2],  # ws_link 
            args[3],  # meeting_id
        )
        #
        # subprocess.Popen(
        #     [  # "xvfb-run --listen-tcp --server-num=44 --auth-file=/tmp/xvfb.auth -s "-ac -screen 0 1920x1080x24" /
        #         "python",
        #         str(GSTREAMER_PATH.resolve()),
        #         "--display_num",
        #         f":{args[1]}",
        #         "--startx",
        #         "0",
        #         "--starty",
        #         "0",
        #         "--endx",
        #         "1920",
        #         "--endy",
        #         "1080",
        #         '--meetingId',
        #         args[3]
        #     ])
        print("ran gstreamer")
        thread = threading.Thread(target=google.setup_ws, daemon=True)
        thread.start()
        print("ran setup")

        google.join_meeting()
        print("joined")
        google.record_and_stream()

        while True:
            google.get_participants()
            print("in here")
            google.get_latest_transcription()
            print("in here 2")
            google.check_meeting_ended()
    except Exception as e:
        if google != None and google.websocket != None:
            google.websocket.bot_error()
        raise e
