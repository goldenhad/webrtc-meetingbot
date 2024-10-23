import subprocess
import sys
import threading
from datetime import datetime
from os import environ
from pathlib import Path
from time import sleep, time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.meeting.botbase import BotBase
from src.utils.constants import BOT_NAME, OUTLOOK_PWD, OUTLOOK, TEAMS_URL

GSTREAMER_PATH = Path(__file__).resolve().parent / "../utils/webrtc_gstreamer.py"
POLL_RATE = 0.3


class TeamsMeet(BotBase):
    def __init__(self, meeting_link, xvfb_display, ws_link, meeting_id, teams_mail=OUTLOOK, teams_pw=OUTLOOK_PWD):
        self.content = ""
        self.mail_address = teams_mail
        self.password = teams_pw
        self.botname = "BotAssistant"
        self.meeting_link = meeting_link
        self.scraping_section_ids = {}
        self.prev_subject = ""
        self.last_send_transcription = datetime.now()
        self.last_subject_sent_time = time()
        super().__init__(ws_link, xvfb_display, meeting_id)

    def pin_participant(self, participant_name):
        try:
            self.driver.implicitly_wait(1)
            attendeesParent = self.driver.find_element(By.XPATH, "//*[@aria-label='Participants']")
            attendeesContainers = attendeesParent.find_elements(By.XPATH,
                                                                ".//li[@role='presentation' and @data-cid='roster-participant']")

            unpin_buttons = self.driver.find_elements(By.XPATH,
                                                      '//button[@data-track-action-outcome="unpinParticipant"]')
            for button in unpin_buttons:
                button.click()  # unpinning all pinned
                print("unpinning...")
            print("all unpinned")

            print('should pin ' + participant_name)
            for attendee in attendeesContainers:
                name = attendee.find_element(By.XPATH, './/span[contains(@id,"roster-avatar-img")]').text
                print("attendee name " + name)
                if name == participant_name:
                    pinned = attendee.find_elements(By.XPATH, './/svg[@data-cid="roster-participant-pinned"]')
                    print("is attendee pinned?")
                    print(pinned == True)
                    if not pinned:
                        attendee.click()
                        print("clicked on attendee " + name)
                        print("not pinned. should pin")
                        attendee.find_element(By.XPATH, ".//button[@data-cid='ts-participant-action-button']").click()
                        self.driver.find_element(By.XPATH, "//span[text()='Pin for me']").click()
        except:  # stale element may occur
            pass

    def get_latest_transcriptions(self):
        try:
            self.driver.implicitly_wait(2)
            transcription_parent = self.driver.find_element(By.XPATH, '//div[@data-tid="closed-captions-renderer"]')
            transcription_elements = transcription_parent.find_elements(By.XPATH,
                                                                        './/li[contains(@class,"ui-chat__item")]')
            if len(transcription_elements) > 2:
                latest_complete_transcription = transcription_elements[-2]
                authorSpan = latest_complete_transcription.find_element(By.XPATH,
                                                                        ".//span[contains(@class,'ui-chat__message__author')]")
                authorName = authorSpan.text if authorSpan is not None else ""

                contentSpan = latest_complete_transcription.find_element(By.XPATH,
                                                                         './/span[@data-tid="closed-caption-text"]')
                content = contentSpan.text if contentSpan is not None else ""
                if self.content != content:
                    self.websocket.send_transcription(
                        authorName,
                        content,
                        self.last_send_transcription,
                        datetime.now()
                    )
                    self.last_send_transcription = datetime.now()
                    self.content = content
        except Exception as e:  # again, weird exceptions occur
            raise e

    def get_participants(self):
        try:
            attendeesParent = self.driver.find_element(By.XPATH, "//*[@aria-label='Participants']")
            attendeesContainers = attendeesParent.find_elements(By.XPATH,
                                                                ".//li[@role='presentation' and @data-cid='roster-participant']")
            new_list = []
            for attendees in attendeesContainers:
                new_list.append(attendees.find_element(By.XPATH, ".//span[contains(@id,'roster-avatar-img')]").text
                                )

            if len(self.participant_list) < 3:
                if not self.is_timer_running():
                    self.start_timer(120, self.exit_func)
            elif self.is_timer_running():
                self.cancel_timer()
            if self.participant_list != new_list:
                print(new_list)
                self.websocket.send_participants(new_list)

            self.participant_list = new_list
            subject = self.driver.find_element(By.XPATH,
                                               "//*[@data-tid='PinStage-wrapper' or @data-tid='SpeakerStage-wrapper']//*[@data-cid='calling-participant-stream']//div[@data-tid='participant-name-decorator-layer']//span[contains(@class,'StyledText')]").text

            current_time = time()
            elapsed_time = current_time - self.last_subject_sent_time 
            if elapsed_time > 1:
                self.websocket.send_subject(subject)
                self.prev_subject = subject
                self.last_subject_sent_time = current_time
        except:  # may send stale element errors
            pass

    def tlogin(self):
        """
        Login to outlook
        """

        # Login Page
        self.driver.implicitly_wait(100)
        self.driver.maximize_window()
        self.driver.get("https://login.live.com/login.srf")
        # input outlook mail

        self.driver.find_element(By.XPATH, '//input[@type="email"]').send_keys(self.mail_address)  # enter email
        self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()  # click next

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
        self.driver.implicitly_wait(600)

        self.driver.find_element(By.XPATH, '//div[@title="Microphone"]/div').click()
        cam = self.driver.find_element(By.XPATH, '//div[@title="Camera"]/div') 
        sleep(2)  # wait for camera to be available
        cam.click()

        input_element = self.driver.find_element(By.XPATH, '//input[@type="text"][@placeholder="Type your name"]')

        # Click the input element
        input_element.click()
        input_element.send_keys(BOT_NAME)


        # Click the join button
        self.driver.implicitly_wait(60)
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

            self.driver.implicitly_wait(10)
            self.driver.find_element(By.XPATH, "//div[@data-tid='closed-captions-renderer']")  # wait for cc to open

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

                self.gstreamer_process =  subprocess.Popen([
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
        except Exception as e:
            print("Unexpected error")
            raise (e)
    
    def unpin_all(self):
        try:
            unpin_buttons = self.driver.find_elements(By.XPATH,
                                                      '//button[@data-track-action-outcome="unpinParticipant"]')
            for button in unpin_buttons:
                button.click()  # unpinning all pinned
                print("unpinning...")
            print("all unpinned")
        except Exception as e:
            print("Unpin was called. But most likely no one is pinned!:",e)


    def check_meeting_ended(self):
        try:
            self.driver.find_element(By.XPATH,"//button[@id='hangup-button']")
        except:
            print("no hangup button")
            # no hangup button found. Exit bot
            self.exit_func()

if __name__ == "__main__":
    teams = None
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
        #     "--meetingId",
        #     args[3]
        # ])

        thread = threading.Thread(target=teams.setup_ws, daemon=True)
        thread.start()
        teams.join_meeting()
        teams.record_and_stream()
        while True:
            teams.get_latest_transcriptions()
            teams.get_participants()
            teams.check_meeting_ended()

        print("Ended")
    except Exception as e:
        if teams != None and teams.websocket != None:
            teams.websocket.bot_error()
        raise e
