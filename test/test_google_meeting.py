import subprocess
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
import re
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--use-fake-ui-for-media-stream")
# chrome_options.add_argument("--use-fake-device-for-media-stream")
# chrome_options.add_argument("--use-file-for-fake-video-capture=/home/lasan/vid.mjpeg")
# chrome_options.add_argument("--use-file-for-fake-audio-capture=/home/lasan/aud.wav")

chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('--start-maximized')
chrome_options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.media_stream_mic": 1,
    "profile.default_content_setting_values.media_stream_camera": 1,
    "profile.default_content_setting_values.geolocation": 0,
    "profile.default_content_setting_values.notifications": 1
})

    # Start recording


driver = webdriver.Chrome(chrome_options)
driver.implicitly_wait(30)
meeting_link = "https://teams.microsoft.com/l/meetup-join/19:meeting_M2YxOWRkZTYtMzVlNi00MTA1LWIzZmYtMGE1YzY0ZDg1NWQ0@thread.v2/0?context=%7B%22Tid%22:%22f9fedb8b-e219-4e87-b744-b3e1a7b830da%22,%22Oid%22:%228fb72fed-b5fd-43f9-9dbd-f0c102b3cb03%22%7D"

# try:
#     meeting_id = re.search(r'(?<=wc/)\d+', meeting_link).group()
# except:
#     meeting_id = re.search(r'(?<=j/)\d+', meeting_link).group()
# password = re.search(r'(?<=pwd=)[^&]*', meeting_link).group()

# driver.get(f"https://app.zoom.us/wc/{meeting_id}/join?pwd={password}")
# driver.get("https://videojs.github.io/autoplay-tests/plain/attr/autoplay.html")
driver.get(meeting_link)
# input Gmail
# driver.find_element(By.ID, "identifierId").send_keys("jaredbohan63@gmail.com")
# driver.find_element(By.ID, "identifierNext").click()
driver.implicitly_wait(10)
# driver.find_element(By.XPATH, "//video").click()
#
# # input Password
# driver.find_element(By.XPATH,
#     '//*[@id="password"]/div[1]/div/div[1]/input').send_keys("twinstar0311")
# driver.implicitly_wait(10)
# driver.find_element(By.ID, "passwordNext").click()
# driver.implicitly_wait(10)    
# # go to google home page
# driver.get('https://google.com/')
# driver.implicitly_wait(100)
# print("Gmail login activity: Done")
# driver.get("https://meet.google.com/landing")
#
# driver.find_element(By.XPATH,"//span[text()='New meeting']").click()
# driver.find_element(By.XPATH,"//span[text()='Start an instant meeting']").click()

with open('script.js','r') as file:
    driver.execute_script(file.read())
    print('executed script')
sleep(600)

