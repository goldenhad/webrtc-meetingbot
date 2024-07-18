from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.utils.constants import GMAIL,GMAIL_PWD,GOOGLE_MEETING_LINK
from src.template import script


class JoinGoogleMeet:
    def __init__(self):
        self.mail_address = GMAIL
        self.password = GMAIL_PWD
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

    def Glogin(self):
        # Login Page
        self.driver.get(
            'https://accounts.google.com/ServiceLogin?hl=en&passive=true&continue=https://www.google.com/&ec=GAZAAQ')
    
        # input Gmail
        self.driver.find_element(By.ID, "identifierId").send_keys(self.mail_address)
        self.driver.find_element(By.ID, "identifierNext").click()
        self.driver.implicitly_wait(10)
    
        # input Password
        self.driver.find_element(By.XPATH,
            '//*[@id="password"]/div[1]/div/div[1]/input').send_keys(self.password)
        self.driver.implicitly_wait(10)
        self.driver.find_element(By.ID, "passwordNext").click()
        self.driver.implicitly_wait(10)    
        # go to google home page
        self.driver.get('https://google.com/')
        self.driver.implicitly_wait(100)
        print("Gmail login activity: Done")
        
 
    def turnOffMicCam(self, meet_link):
        # Navigate to Google Meet URL (replace with your meeting URL)
        self.driver.get(meet_link)
        self.driver.implicitly_wait(20)
        # turn off Microphone
        self.driver.find_element(By.CSS_SELECTOR, 'div[jscontroller="t2mBxb"][data-anchor-id="hw0c9"]').click()
        self.driver.implicitly_wait(3000)
        print("Turn off mic activity: Done")
    
        # turn off camera
        sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, 'div[jscontroller="bwqwSd"][data-anchor-id="psRWwc"]').click()
        self.driver.implicitly_wait(3000)
        print("Turn off camera activity: Done")
 
 
    def checkIfJoined(self):
        try:
            print("Check if join try")

            # Wait for the join button to appear
            spotlighted= WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'video'))
            )
            print(spotlighted)

            print("Meeting has been joined")
        except (TimeoutException, NoSuchElementException):
            print("Meeting has not been joined")

    
    def AskToJoin(self):
        # Ask to Join meet
        self.driver.implicitly_wait(2000)
        self.driver.find_element(By.CSS_SELECTOR, 'button[jsname="Qx7uuf"]').click()
        print("Ask to join activity: Done")
        self.checkIfJoined()
        # Ask to join and join now buttons have same xpaths

    def Record(self,time):
        print("Record Start")
        video_elements = self.driver.find_elements(By.XPATH,"//video")
        print("Record Start")

        element = None
        for l in video_elements:
            if l.is_displayed:
                self.driver.execute_script(script,l)
                print("executed")
                sleep(time)

        # driver.execute_script(script,driver.find_elements(By.XPATH,"//div")[0])
        print("Finished loopping through elmenets")

def main():
    # temp_dir = tempfile.mkdtemp()
    audio_path = "output.wav"
    # Duration for bot to record audio
    meet_link = GOOGLE_MEETING_LINK
    duration = 60
    obj = JoinGoogleMeet()
    obj.Glogin()
    obj.turnOffMicCam(meet_link)
    obj.AskToJoin(audio_path, duration)
    obj.Record(35)
    
    sleep(600)

#call the main function
if __name__ == "__main__":
    main()