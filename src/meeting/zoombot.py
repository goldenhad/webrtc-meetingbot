# import required modules
from dotenv import load_dotenv
import difflib
import re
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from time import sleep, time

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.meeting.botbase import BotBase

WAIT_ADMIT_TIME = 120
POLL_RATE = 0.3
GSTREAMER_PATH = Path(__file__).resolve().parent / "../utils/webrtc_gstreamer.py"
load_dotenv("/home/lasan/Dev/trustlehubgit/.env")


class ZoomMeet(BotBase):
    def __init__(self, meeting_link, xvfb_display, ws_link, meeting_id, zoom_email="", zoom_password=""):
        self.zoom_email = zoom_email
        self.zoom_password = zoom_password
        self.botname = "BotAssistant"
        self.meeting_link = meeting_link
        self.last_transcription = ""
        self.last_transcription_sent = datetime.now()
        self.prev_subject = ""
        self.last_subject_sent_time = time()
        self.transcription_popup_cleared = False
        super().__init__(ws_link, xvfb_display, meeting_id)

    def check_transcription_popup(self):
        try:
            self.driver.implicitly_wait(10)
            self.driver.find_element(By.XPATH,"//*[@class='zm-modal-body-title' and text()='This meeting is being transcribed.']")
            self.driver.find_element(By.XPATH,"//button[text()='OK']").click()
            self.transcription_popup_cleared = True
            self.driver.implicitly_wait(2)
        except:
            pass


    def join_meeting(self):
        print(self.xvfb_display)
        print(self.meeting_link)
        try:
            meeting_id = re.search(r'(?<=wc/)\d+', self.meeting_link).group()
        except:
            meeting_id = re.search(r'(?<=j/)\d+', self.meeting_link).group()
        password = re.search(r'(?<=pwd=)[^&]*', self.meeting_link).group()

        self.driver.get(f"https://app.zoom.us/wc/{meeting_id}/join?pwd={password}")

        self.driver.maximize_window()

        try: # region depenedent
            self.driver.implicitly_wait(10)
            self.driver.find_element(By.XPATH, "//button[@id='onetrust-accept-btn-handler']").click()

            self.driver.find_element(By.XPATH, '//button[@id="wc_agree1"]').click()
        except: # this section is region depended. In EU, this is required
            pass
        #

        self.driver.implicitly_wait(60)
        self.driver.find_element(By.ID, 'input-for-name').send_keys(self.botname)

        self.driver.implicitly_wait(10)
        join_button = self.driver.find_element(By.XPATH, '//button[contains(@class, "preview-join-button")]')

        # Click the join button
        sleep(5)
        join_button.click()

        # waiting till joined
        # Wait for the SVG with class "SvgShare" to appear
        self.driver.implicitly_wait(WAIT_ADMIT_TIME)
        self.driver.find_element(By.CLASS_NAME, 'SvgShare')

        self.check_transcription_popup()

        # Wait for the element with text "Join Audio by Computer" to appear
        join_audio_button = WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//*[text()="Join Audio by Computer"]'))
        )
        sleep(5)

        # Click the join audio button
        if join_audio_button.is_enabled() and join_audio_button.is_displayed():
            # Click the join audio button
            join_audio_button.click()

        sleep(5)
        more_button = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'moreButton'))
        )

        # Click the more button twice. zoom issue
        more_button.click()
        sleep(2)
        more_button.click()

        self.driver.find_element(By.XPATH, '//a[@aria-label="Settings"]').click()

        meeting_controls = self.driver.find_element(By.XPATH, '//div[text()="Always show meeting controls"]/..')
        if meeting_controls.get_attribute("aria-checked") != "true":
            meeting_controls.click()

        self.driver.find_element(By.XPATH, '//button[contains(@class,"zm-btn settings-dialog__close")]').click()


        # enable close captions
        more_button = self.driver.find_element(By.ID, 'moreButton')
        # Click the more button twice. zoom issue
        more_button.click()
        sleep(2)
        more_button.click()

        try:
            self.driver.implicitly_wait(10)
            self.driver.find_element(By.XPATH, "//a[text()='Captions']").click()
            self.driver.find_element(By.XPATH, "//a[text()='Show Captions']").click()
            l = self.driver.find_elements(By.XPATH,"//span[text()='Caption Language']")
            if len(l) > 0:
                self.driver.find_element(By.XPATH,"//button[text()='Save']").click()
        except Exception as e:
            print("captions are probably already enabled")

        print("Joined to meeting")

    def record_and_stream(self):
        self.driver.implicitly_wait(10)
        self.driver.find_element(By.XPATH, "//span[text()='View']").click()

        self.driver.find_element(By.XPATH, "//a[text()='Speaker View']").click()

        # need to click twice. Zoom bug
        self.driver.find_element(By.XPATH, '//div[@feature-type="participant"]').click()
        sleep(2)
        self.driver.find_element(By.XPATH, '//div[@feature-type="participant"]').click()

        sleep(2)  # give some time for the viewport to adjust before getting coords

        panel_height = self.driver.execute_script('return window.outerHeight - window.innerHeight;')

        self.driver.implicitly_wait(60)
        height, width, x, y = self.driver.find_element(By.XPATH,
                                                       "//div[@class='speaker-active-container__video-frame']").rect.values()
        y += panel_height
        self.height = height
        self.width = width
        self.x = x
        self.y = y

        self.websocket.send_analysing(
            self.meeting_id,
            self.inference_id
        )

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

        print("ran gstreamer")

    def pin_participant(self, participant_name) -> None:
        print("pin called: ",participant_name)
        try:

            self.driver.implicitly_wait(5)
            self.driver.find_element(By.XPATH, '//div[contains(@class,"participants-section-container")]')
            search_available = True
            participant_search = None
            try:
                participant_search = self.driver.find_element(By.XPATH,
                                                              '//input[contains(@class,"participants-search-box__input")]')
            except:
                search_available = False

            if search_available and participant_search != None:
                print("search available")
                participant_search.send_keys(100 * "\b")
                participant_search.send_keys(participant_name)
                participant_list = self.driver.find_elements(By.XPATH, "//div[@class='participants-item-position']")
                for element in participant_list:
                    # its ok to just loop through this. Search has already filterd it out

                    ActionChains(self.driver).move_to_element(element).click().perform()
                    sleep(3)
                    more_button = element.find_element(By.XPATH, ".//span[text()='More']")

                    self.driver.implicitly_wait(0)  # remove implicit wait before setting explicit. Should not mix both
                    WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(more_button)
                    )
                    more_button.click()
                    self.driver.implicitly_wait(2)

                    try:
                        self.driver.find_element(By.XPATH, '//button[text()="Replace Pin"]').click()
                        print("got replace")
                    except (NoSuchElementException, TimeoutException):
                        self.driver.find_element(By.XPATH, '//button[text()="Add Pin"]').click()
                        print("got add ")
                    except Exception as e:
                        print("add / replace pin button not found")
                        print(e)
                participant_search.send_keys(len(participant_name) * "\b")
            else:
                print("no search available")
                participant_list = self.driver.find_elements(By.XPATH, "//div[@class='participants-item-position']")
                for element in participant_list:
                    name = element.find_element(By.XPATH, ".//span[@class='participants-item__display-name']").text
                    print('current name: ',name)
                    if name in participant_name:
                        print("name in participant name")
                        ActionChains(self.driver).move_to_element(element).click().perform()
                        sleep(1)
                        more_button = element.find_element(By.XPATH, ".//span[text()='More']")

                        self.driver.implicitly_wait(
                            0)  # remove implicit wait before setting explicit. Should not mix both
                        WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable(more_button)
                        )
                        more_button.click()
                        print("clicked more")
                        self.driver.implicitly_wait(2)

                        try:
                            self.driver.find_element(By.XPATH, '//button[text()="Replace Pin"]').click()
                            print("got replace")
                        except (NoSuchElementException, TimeoutException):
                            self.driver.find_element(By.XPATH, '//button[text()="Add Pin"]').click()
                            print("got add ")
                        except Exception as e:
                            print("add / replace pin button not found")
                            print(e)

        except Exception as e:
            self.driver.save_screenshot("spotlight_error.png")
            print(e)

    def get_latest_transcriptions(self):
        try:
            self.driver.implicitly_wait(10)
            cc_box = self.driver.find_element(By.XPATH, "//div[contains(@class,'live-transcription-subtitle__box')]")
            self.driver.implicitly_wait(1)
            subtitles = cc_box.find_elements(By.ID, 'live-transcription-subtitle')

            if len(subtitles) > 0:
                text = subtitles[-1].text
                if text != self.last_transcription:

                    diff = difflib.ndiff(text, self.last_transcription)
                    diff_list = [char for char in diff if char.startswith('- ')]
                    diff_text =  ''.join(char[2:] for char in diff_list)
                    self.websocket.send_transcription(
                        "",
                        diff_text,
                        self.last_transcription_sent,
                        datetime.now()

                    )
                    self.last_transcription = text
                    self.last_transcription_sent = datetime.now()
        except:
            pass
    def get_participants(self):
        try:
            updated = False
            participant_list = self.driver.find_elements(By.XPATH, "//div[@class='participants-item-position']")
            if len(participant_list) < 3:
                if not self.is_timer_running():
                    self.start_timer(120, self.exit_func)
            elif self.is_timer_running():
                self.cancel_timer()

            for element in participant_list:
                name = element.find_element(By.XPATH, ".//span[@class='participants-item__display-name']").text
                if name not in self.participant_list:
                    self.participant_list.append(name)
                    updated = True
            if updated:
                self.websocket.send_participants(self.participant_list)

            # getting subject
            subject = self.driver.find_element(By.XPATH,
                                     "//div[@class='speaker-active-container__video-frame']//div[@class='video-avatar__avatar-footer']//span").text

            current_time = time()
            elapsed_time = current_time - self.last_subject_sent_time 
            if elapsed_time > 1:
                self.websocket.send_subject(subject)
                self.prev_subject = subject
                self.last_subject_sent_time = current_time

        except Exception as e: 
            print("Probably a stale elemenet error")
            print(e)
            pass

    def unpin_all(self):
        try:
            video_element = self.driver.find_element(By.XPATH,
                                                       "//div[@class='speaker-active-container__video-frame']")
            ActionChains(self.driver).move_to_element_with_offset(video_element,30,30).click().perform()
            self.driver.find_element(By.XPATH,"//button[text()='Remove Pin']").click()

        except Exception as e:
            print("Unpin was called. But most likely no one is pinned!:",e)

    def check_meeting_ended(self):
        try:
            self.driver.find_element(By.CLASS_NAME, 'SvgShare')
            self.driver.implicitly_wait(2)
            meeting_ended= self.driver.find_elements(By.XPATH, '//div[@aria-label="Meeting is end now"]')
            removed= self.driver.find_elements(By.XPATH, '//div[@aria-label="You have been removed"]')
            if meeting_ended or removed:
                raise Exception("Meeting ended")
        except:
            print("meeting probably ended")
            # SvgShare icon isn't found. probably quit meeting. 
            self.exit_func()

        
if __name__ == "__main__":
    zoom = None
    try:
        args = sys.argv[1:]
        zoom = ZoomMeet(args[0],  # meeting url
                        args[1],  # xvfb numner 
                        args[2],  # ws_link 
                        args[3],  # meeting_id
                        )
        print("ran")
        thread = threading.Thread(target=zoom.setup_ws, daemon=True)
        thread.start()
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
        #         'b1786fdc-1120-41a5-8f7c-3deebdcdd71f'
        #     ])
        zoom.join_meeting()
        zoom.record_and_stream()
        while True:
            zoom.get_latest_transcriptions()
            zoom.get_participants()
            zoom.check_meeting_ended()


    except Exception as e:
        if zoom != None and zoom.websocket != None:
            zoom.websocket.bot_error()
        raise e

    # Main event loop for zoombot
