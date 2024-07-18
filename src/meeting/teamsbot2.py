from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

OUTLOOK="test20240717@outlook.com"
OUTLOOK_PWD="meetingbot2024"
TEAMS_URL="https://teams.microsoft.com/_#/calendarv2"
TEAMS_MEETING_LINK='https://teams.live.com/meet/932011034979?p=fRClkxbrCli8WyFIhc'
# from src.template import script

# from src.utils.constants import OUTLOOK,OUTLOOK_PWD,GOOGLE_MEETING_LINK,TEAMS_URL
# from src.template import script

class JoinTeamsMeet:
    def __init__(self):
        self.mail_address = OUTLOOK
        self.password = OUTLOOK_PWD
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

    def wait_and_find_ele_by_id(self,html_id, timeout=60):
        sleep(1)
        for i in range(timeout):
            try:
                # ele = browser.find_element_by_id(html_id)
                ele = self.driver.find_element(by=By.ID, value=html_id)
            except:
                sleep(3)
            else:
                return ele
    def wait_and_find_ele_by_link_text(self,text, timeout=60):
        sleep(1)
        for i in range(timeout):
            try:
                # ele = browser.find_element_by_link_text(text)
                ele = self.driver.find_element(by=By.LINK_TEXT, value=text)
            except:
                sleep(3)
            else:
                return ele
    def wait_and_find_element_by_xpath(self,xpath, timeout=60):
        sleep(1)
        for i in range(timeout):
            try:
                # ele = browser.find_element_by_xpath(xpath)
                ele = self.driver.find_element(by=By.XPATH, value=xpath)
            except:
                sleep(3)
            else:
                return ele
            
    def Tlogin(self):
        # Login Page
        self.driver.get(TEAMS_URL)
        # sleep(3)  # 3 sec delay
        self.driver.implicitly_wait(100)
        # input outlook mail
        self.wait_and_find_ele_by_id('i0116').send_keys(self.mail_address)  # enter email
        self.wait_and_find_ele_by_id('idSIButton9').click()  # click next
        self.wait_and_find_ele_by_id('i0118').send_keys(self.password)  # enter password
        self.wait_and_find_ele_by_id('idSIButton9').click()  # click next
        self.wait_and_find_ele_by_id('acceptButton').click()  # click yes to stay signed in
        web_ele = self.wait_and_find_ele_by_link_text('Use the web app instead', 5)
        if web_ele is not None:
            web_ele.click()

        print("Outlook login activity: Done")
        
 
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
 
 
    def join_meeting(self):
        # Open Meeting Link
        self.driver.get(TEAMS_MEETING_LINK)  
        # _log("Started Browser")

        # Get meeting url directly
        ## Wait until the URL changes (indicating redirection)
        redirected_url = WebDriverWait(self.driver,3).until(
            EC.url_changes(TEAMS_MEETING_LINK)
        )
        ## Once redirected, retrieve the current URL
        final_url = self.driver.current_url
        print(f"Got direct url :{final_url}")

        # Open a new tab and navigate to a new URL
        self.driver.execute_script("window.open('about:blank', 'new_tab')")
        new_tab_handle = self.driver.window_handles[-1]  # Switch to the newly opened tab
        self.driver.switch_to.window(new_tab_handle)
        self.driver.get(final_url)
        print(f"Opened new tab")
        
        # Click join by web button
        self.wait_and_find_element_by_xpath('//button[@data-tid="joinOnWeb"]').click()  # join by Web

        sleep(30)    
        print(f"Click the join on web button")
        # If the element is inside an iframe, switch to the iframe first
        try:
            iframe = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'iframe'))
            )
            self.driver.switch_to.frame(iframe)
            print("Switched to iframe")
        except TimeoutException:
            print("Failed to find the iframe within the given time.")

        print(f"Enter bot username")

        # Enter username (Only working in guest Mode)
        # wait_and_find_element_by_xpath('//input[@data-tid="prejoin-display-name-input"]').send_keys(config["nickname"])  
        
        self.wait_and_find_ele_by_id('prejoin-join-button').click()  # join meeting

        # Wait for Main Meeting Page
        try:
            iframe = WebDriverWait(self.driver, 1800).until(
                EC.presence_of_element_located((By.ID, 'hangup-button'))
            )
            self.driver.switch_to.frame(iframe)
            print("Joined to Meeting")
        except TimeoutException:
            print("Failed to join the meeting")


        print("Joined Meeting")
      
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
    # meet_link = GOOGLE_MEETING_LINK
    obj = JoinTeamsMeet()
    obj.Tlogin()
    obj.join_meeting()
    # obj.turnOffMicCam(meet_link)
    # obj.AskToJoin(audio_path, duration)
    # obj.Record(35)
    
    sleep(600)

#call the main function
if __name__ == "__main__":
    main()