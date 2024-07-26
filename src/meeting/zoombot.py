# import required modules
from uuid import uuid4
import argparse
import re
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from src.utils.websocketmanager import WebsocketConnection
from os import environ

WAIT_ADMIT_TIME = 120

class JoinZoomMeet:
    def __init__(self, meeting_link, zoom_email, zoom_password, xvfb_display, ws_link, meeting_id):
        self.zoom_email = zoom_email
        self.zoom_password = zoom_password
        self.xvfb_display = xvfb_display
        self.botname = "BotAssistant"  
        self.meeting_id = meeting_id
        self.meeting_link = meeting_link
        self.inference_id = uuid4()
        self.scraping_section_ids = {}
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
        self.socket = WebsocketConnection(ws_link)

    def join_meeting(self):
        try:
            meeting_id = re.search(r'(?<=wc/)\d+', self.meeting_link).group()
        except:
            meeting_id = re.search(r'(?<=j/)\d+', self.meeting_link).group()
        password = re.search(r'(?<=pwd=)[^&]*', self.meeting_link).group()


        self.driver.get(f"https://app.zoom.us/wc/{meeting_id}/join?pwd={password}")

        if not hasattr(environ,"DEV"):
            self.driver.implicitly_wait(10)
            self.driver.find_element(By.XPATH, "//button[@id='onetrust-accept-btn-handler']").click()

            self.driver.find_element(By.XPATH, '//button[@id="wc_agree1"]').click()


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

        more_button = self.driver.find_element(By.ID, 'moreButton')
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

        active_speaker = self.driver.find_element(By.XPATH,"//div[@class='speaker-active-container__video-frame']")

        # need to click twice. Zoom bug
        self.driver.find_element(By.XPATH, '//div[@feature-type="participant"]').click()
        sleep(5)
        self.driver.find_element(By.XPATH, '//div[@feature-type="participant"]').click()

        panel_height = self.driver.execute_script('return window.outerHeight - window.innerHeight;')

        height, width, x, y = active_speaker.rect.values()
        y += panel_height

        self.height = height
        self.width = width 
        self.x = x
        self.y = y

        self.socket.send_analysing(
            self.meeting_id,
            self.inference_id
        )


    def pin_participant(self, participant_name) -> None:
        try:

            self.driver.implicitly_wait(10)
            self.driver.find_element(By.XPATH, '//div[contains(@class,"participants-section-container")]')
            search_available = True
            participant_search = None
            try:
                participant_search = self.driver.find_element(By.XPATH, '//input[contains(@class,"participants-search-box__input")]')
            except:
                search_available = False


            if search_available and participant_search != None:
                participant_search.send_keys(100*"\b")
                participant_search.send_keys(participant_name)
                participant_list = self.driver.find_elements(By.XPATH,"//div[@class='participants-item-position']")
                for element in participant_list:
                    ActionChains(self.driver).move_to_element(element).click().perform()
                    sleep(3)
                    more_button = element.find_element(By.XPATH,".//span[text()='More']")
                    
                    self.driver.implicitly_wait(0) # remove implicit wait before setting explicit. Should not mix both
                    WebDriverWait(self.driver,5).until(
                        EC.element_to_be_clickable(more_button)
                    )
                    more_button.click()
                    self.driver.implicitly_wait(10)

                    try:
                        replace_pin_button = self.driver.find_element(By.XPATH, '//button[text()="Replace Pin"]')

                        if replace_pin_button:
                            element = replace_pin_button
                        else:
                            # If "Replace Pin" button is not found, try to find the "Add Pin" button
                            add_pin_button = self.driver.find_element(By.XPATH, '//button[text()="Add Pin"]')
                            if add_pin_button:
                                element = add_pin_button
                            else:
                                element = None
                        element.click() if element != None else None
                    except TimeoutException:
                        print("add / replace pin button not found")
                participant_search.send_keys(len(participant_name)*"\b")
            else:
                participant_list = self.driver.find_elements(By.XPATH,"//div[@class='participants-item-position']")
                for element in participant_list:
                    ActionChains(self.driver).move_to_element(element).click().perform()
                    sleep(3)
                    more_button = element.find_element(By.XPATH,".//span[text()='More']")

                    self.driver.implicitly_wait(0) # remove implicit wait before setting explicit. Should not mix both
                    WebDriverWait(self.driver,5).until(
                        EC.element_to_be_clickable(more_button)
                    )
                    more_button.click()
                    self.driver.implicitly_wait(10)

                    try:
                        replace_pin_button = self.driver.find_element(By.XPATH, '//button[text()="Replace Pin"]')

                        if replace_pin_button:
                            element = replace_pin_button
                        else:
                            # If "Replace Pin" button is not found, try to find the "Add Pin" button
                            add_pin_button = self.driver.find_element(By.XPATH, '//button[text()="Add Pin"]')
                            if add_pin_button:
                                element = add_pin_button
                            else:
                                element = None
                        element.click() if element != None else None
                    except TimeoutException:
                        print("add / replace pin button not found")

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



def main():
    parser = argparse.ArgumentParser(description="Process some arguments.")
    parser.add_argument('--wbsocket_url', type=str, required=True, help='WebSocket URL')
    parser.add_argument('--zoom_email', type=str, required=True, help='Zoom email')
    parser.add_argument('--zoom_password', type=str, required=True, help='Zoom password')
    parser.add_argument('--xvfb_display', type=int, required=True, help='Xvfb display number')

    args = parser.parse_args()

    print(f"WebSocket URL: {args.wbsocket_url}")
    print(f"Zoom Email: {args.zoom_email}")
    print(f"Zoom Password: {args.zoom_password}")
    print(f"Xvfb Display Number: {args.xvfb_display}")

if __name__ == "__main__":
    main()
