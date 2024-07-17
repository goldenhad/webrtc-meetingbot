# import required modules
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
# from record_audio import AudioRecorder
# from speech_to_text import SpeechToText
import os
import tempfile     

class JoinZoomMeet:
    def __init__(self,meetinglink):
        self.botname = "BotAssistanct"  
        self.meetingLink = meetinglink
        # create chrome instance
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

    def Zlogin(self):
        # Login Page
        webJoinLink = self.meetingLink.replace("us05web.zoom.us/j","app.zoom.us/wc/join")
        print(webJoinLink)
        self.driver.get(webJoinLink)

        # input Botname
        self.driver.implicitly_wait(10)
        self.driver.find_element(By.ID, "input-for-name").send_keys(self.botname)
        self.driver.implicitly_wait(10)
        self.driver.find_element(By.XPATH,"//button[contains(@class,'preview-join-button')]").click()
        self.driver.implicitly_wait(100)
        self.driver.find_element(By.XPATH,"//button[contains(@aria-label,'close')]").click()
        sleep(100)
        
        print("Joined to meeting")


    
def main():
    meet_link = 'https://us05web.zoom.us/j/89844356536?pwd=Wk0AvmRTfTYXWaDce1zjlqg90QWudi.1'
    obj = JoinZoomMeet(meet_link)
    obj.Zlogin()


#call the main function
if __name__ == "__main__":
    main()