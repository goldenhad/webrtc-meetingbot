# import required modules
import asyncio
import subprocess
from uuid import uuid4
import sys
import websockets
import re
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
from os import environ
from datetime import datetime
from typing import Callable, List
from pydantic import UUID4
import json

WAIT_ADMIT_TIME = 120
GSTREAMER_PATH = Path(__file__).resolve().parent / "../utils/zoom_gstreamer.py"

class WebsocketConnection:
    def __init__(self,ws_link: str) -> None:
        self.ws_link: str = ws_link
        self.ws = None
        self.analysing_sent: bool = False
        self.room_joined: bool = False
        self.connected: bool = False


    async def connect(self):
        self.conn = await websockets.connect(self.ws_link)
        await self.conn.send(json.dumps({
            'event':"join-room",
            'room':"room1"   
        }))

    def __ws_send(self,payload: dict):
        if self.ws != None:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.ws.send(json.dumps(payload)))

            
    def join_room(self, room_id: str, start_time: datetime, inference_id: UUID4):
        payload = {
            "event": "join-room",
            "data": {"roomId":room_id,"startTime": start_time, "inferenceId": inference_id}
        }
        if not self.room_joined:
            self.__ws_send(payload)

    def send_transcription(self, name: str, content: str, start: datetime, end: datetime):
        payload = {
            "event": "transcription",
            "data": {"name":name,"content": content, "timeStamps": {
                "start": start,
                "end": end
            }}
        }
        self.__ws_send(payload)

    def bot_error(self):
        payload = {
            "event": "extension-bot-error"
        }
        self.__ws_send(payload)


    def send_analysing(self, meeting_id: str, inference_id: UUID4, rtmp_url: str = ""):
        payload = {
            "event": "analysing",
            "data": {
                "meetingId": meeting_id,
                "inferenceId": inference_id,
                "rtmpUrl": rtmp_url,
            }
        }
        if not self.analysing_sent:
            self.__ws_send(payload)
            self.analysing_sent = True

    def send_participants(self, participants: List[str]):
        payload = {
            "event": "participants",
            "data": participants
        }
        self.__ws_send(payload)

    def send_subject(self, subject: str):
        payload = {
            "event": "subject",
            "data": subject
        }
        self.__ws_send(payload)

    def close(self):
        if self.ws != None:
            self.ws.close()
            self.connected = False

class ZoomMeet:
    def __init__(self, meeting_link, xvfb_display, ws_link, meeting_id, zoom_email="", zoom_password=""):
        self.zoom_email = zoom_email
        self.zoom_password = zoom_password
        self.xvfb_display = xvfb_display
        self.botname = "BotAssistant"  
        self.meeting_id = meeting_id
        self.meeting_link = meeting_link
        self.inference_id = uuid4()
        self.scraping_section_ids = {}
        self.websocket = WebsocketConnection(ws_link)

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
        self.socket = WebsocketConnection(ws_link)

    async def loop(self):
        async for message in self.websocket.conn:    
            msg: dict = json.loads(message)
            print(msg)
            event = msg["event"]

            if event == "select-subject":
                print("need to call pin participant")
                self.pin_participant(msg['data'])
                print("finished pin participant func")
        return 0

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
        # if not hasattr(environ,"DEV"):
        #     self.driver.implicitly_wait(10)
        #     self.driver.find_element(By.XPATH, "//button[@id='onetrust-accept-btn-handler']").click()
        #
        #     self.driver.find_element(By.XPATH, '//button[@id="wc_agree1"]').click()
        #

        self.driver.implicitly_wait(60)
        self.driver.find_element(By.ID, 'input-for-name').send_keys(self.botname)


        self.driver.implicitly_wait(10)
        join_button = self.driver.find_element(By.XPATH, '//button[contains(@class, "preview-join-button")]')

        # Click the join button
        sleep(5)
        join_button.click()

        #waiting till joined
        # Wait for the SVG with class "SvgShare" to appear
        self.driver.implicitly_wait(WAIT_ADMIT_TIME)
        self.driver.find_element(By.CLASS_NAME, 'SvgShare')

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
        sleep(5)
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
        sleep(5)
        more_button.click()

        try:
            self.driver.find_element(By.XPATH,"//a[text()='Captions']").click()
            self.driver.find_element(By.XPATH,"//a[text()='Show Captions']").click()
        except Exception as e:
            print(e)
            
        print("Joined to meeting")

    def record_and_stream(self):
        self.driver.implicitly_wait(10)  
        self.driver.find_element(By.XPATH,"//span[text()='View']").click()

        self.driver.find_element(By.XPATH,"//a[text()='Speaker View']").click()


        # need to click twice. Zoom bug
        self.driver.find_element(By.XPATH, '//div[@feature-type="participant"]').click()
        sleep(5)
        self.driver.find_element(By.XPATH, '//div[@feature-type="participant"]').click()

        sleep(5) # give some time for the viewport to adjust before getting coords

        panel_height = self.driver.execute_script('return window.outerHeight - window.innerHeight;')

        height, width, x, y = self.driver.find_element(By.XPATH,"//div[@class='speaker-active-container__video-frame']").rect.values()
        y += panel_height

        self.height = height
        self.width = width 
        self.x = x
        self.y = y

        self.socket.send_analysing(
            self.meeting_id,
            self.inference_id
        )

        subprocess.Popen([
            # "xvfb-run --listen-tcp --server-num=44 --auth-file=/tmp/xvfb.auth -s "-ac -screen 0 1920x1080x24" /
            "python",
            str(GSTREAMER_PATH.resolve()),
            "--display_num",
            f":{self.xvfb_display}",
            "--startx",
            str(x),
            "--starty",
            str(y),
            "--endx",
            str(x+width),
            "--endy",
            str(y+height)
        ])

        self.websocket.send_analysing(self.meeting_id,self.inference_id)
        print("ran gstreamer")

    def pin_participant(self, participant_name) -> None:
        print("pin called")
        print(participant_name)
        try:
            
            self.driver.implicitly_wait(5)
            self.driver.find_element(By.XPATH, '//div[contains(@class,"participants-section-container")]')
            search_available = True
            participant_search = None
            try:
                participant_search = self.driver.find_element(By.XPATH, '//input[contains(@class,"participants-search-box__input")]')
            except:
                search_available = False


            if search_available and participant_search != None:
                print("search available")
                participant_search.send_keys(100*"\b")
                participant_search.send_keys(participant_name)
                participant_list = self.driver.find_elements(By.XPATH,"//div[@class='participants-item-position']")
                for element in participant_list:
                    # its ok to just loop through this. Search has already filterd it out

                    ActionChains(self.driver).move_to_element(element).click().perform()
                    sleep(3)
                    more_button = element.find_element(By.XPATH,".//span[text()='More']")
                    
                    self.driver.implicitly_wait(0) # remove implicit wait before setting explicit. Should not mix both
                    WebDriverWait(self.driver,5).until(
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
                participant_search.send_keys(len(participant_name)*"\b")
            else:
                print("no search available")
                participant_list = self.driver.find_elements(By.XPATH,"//div[@class='participants-item-position']")
                for element in participant_list:
                    name = element.find_element(By.XPATH,".//span[@class='participants-item__display-name']").text
                    print(name)
                    if name in  participant_name:
                        print("name in participant name")
                        ActionChains(self.driver).move_to_element(element).click().perform()
                        sleep(1)
                        more_button = element.find_element(By.XPATH,".//span[text()='More']")

                        self.driver.implicitly_wait(0) # remove implicit wait before setting explicit. Should not mix both
                        WebDriverWait(self.driver,5).until(
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
        self.driver.implicitly_wait(10)
        cc_box = self.driver.find_element(By.XPATH,"//div[contains(@class,'live-transcription-subtitle__box')]")
        subtitles = cc_box.find_elements(By.ID,'live-transcription-subtitle') 

        for subtitle_container in subtitles:
            scraping_id = subtitle_container.get_attribute("scraping-id")
            if scraping_id != None:
                if scraping_id not in self.scraping_section_ids.keys():
                    self.scraping_section_ids[scraping_id] = subtitle_container.text
                elif subtitle_container.text != self.scraping_section_ids[scraping_id]:
                    pass # send to backend
            else:
                generated_scraping_id = str(uuid4()) 
                self.driver.execute_script("arguments[0].setAttribute('scraping-id',arguments[1]);",subtitle_container,generated_scraping_id)
                self.scraping_section_ids[generated_scraping_id] = subtitle_container.text

if __name__ == "__main__":
    args = sys.argv[1:]

    zoom = ZoomMeet(args[0], # meeting url
                    args[1], # xvfb numner 
                    args[2], # ws_link 
                    args[3], # meeting_id
                    )
    print("ran")
    zoom.join_meeting()
    zoom.record_and_stream()
    asyncio.get_event_loop().run_until_complete(zoom.websocket.connect())
    res = asyncio.get_event_loop().run_until_complete(zoom.loop())
