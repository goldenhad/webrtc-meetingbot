import json
from uuid import uuid4

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import threading

from src.utils.websocketmanager import WebsocketConnection


class BotBase:

    def __init__(self, ws_link, xvfb_display, meeting_id):
        self.timer = None
        self.timer_running = False
        self.ws_link = ws_link
        self.driver = None
        self.websocket = WebsocketConnection(self.ws_link)
        self.participant_list = []
        self.xvfb_display = xvfb_display
        self.inference_id = uuid4()
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

    def setup_ws(self):
        self.websocket.connect()
        self._loop()

    def _loop(self):
        while self.websocket.conn:
            message = self.websocket.conn.recv()
            msg: dict = json.loads(message)
            event = msg["event"]

            if event == "select-subject":
                print("need to call pin participant")
                self.pin_participant(msg['data'])
                print("finished pin participant func")

    def exit_func(self):
        # self.driver.quit()
        print("should quit")

    def pin_participant(self, participant_name):
        pass