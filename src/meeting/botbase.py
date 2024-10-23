import json
from subprocess import Popen
import sys
from uuid import uuid4

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import threading

from selenium.webdriver.chrome.webdriver import WebDriver

from src.utils.websocketmanager import WebsocketConnection


class BotBase:
    def __init__(self, ws_link, xvfb_display, meeting_id):
        self.timer = None
        self.timer_running = False
        self.ws_link = ws_link
        self.driver = None
        self.websocket = WebsocketConnection(self.ws_link, meeting_id)
        self.participant_list = []
        self.xvfb_display = xvfb_display
        self.inference_id = uuid4()
        self.meeting_id = meeting_id
        self.timer = None
        self.timer_running = False
        self.gstreamer_process: Popen | None = None
        # Create Chrome instance
        opt = Options()
        opt.add_argument('--disable-blink-features=AutomationControlled')
        opt.add_argument('--no-sandbox')
        opt.add_argument('--start-maximized')
        opt.add_argument('--use-fake-device-for-media-stream')

        opt.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.geolocation": 0,
            "profile.default_content_setting_values.notifications": 1
        })
        self.driver: WebDriver = webdriver.Chrome(options=opt)
        self.driver.maximize_window()

    def start_timer(self, interval, func):
        # Cancel any existing timer before starting a new one
        if self.timer_running:
            self.cancel_timer()

        print("Starting timer...")
        self.timer = threading.Timer(interval, func)
        self.timer.daemon = True
        self.timer.start()
        self.timer_running = True

    def cancel_timer(self):
        if self.timer is not None:
            print("Cancelling timer...")
            self.timer.cancel()
        self.timer_running = False

    def is_timer_running(self):
        return self.timer_running

    def setup_ws(self):
        def any_event(event,data):
            msg = data
            print("botbase: ",event)
            if event == "select-subject":
                print("need to call pin participant")
                participant_name = msg['data']
                if participant_name == "":
                    self.unpin_all()
                else:
                    self.pin_participant(msg['data'])
                print("finished pin participant func")

        self.websocket.sio.on("*",any_event)
        self.websocket.connect()

    def exit_func(self):
        self.driver.quit()
        print("should quit")
        try:
            self.gstreamer_process.kill()
        except Exception as e:
            print('error: ',e)
        finally:
            sys.exit(0)

    def pin_participant(self, participant_name):
        pass
    
    def check_meeting_ended(self):
        pass

    def unpin_all(self):
        pass
