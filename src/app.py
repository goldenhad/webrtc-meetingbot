from multiprocessing import Process
from pathlib import Path
import subprocess
from time import sleep
import random
from fastapi import FastAPI 
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from src.meeting.googlebot import GoogleMeet
from src.meeting.teamsbot import TeamsMeet
from src.types import CallMeeting
from src.utils.constants import WEBSOCKET_URL


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Can alter with time
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ZOOM_SCRIPT_PATH = Path(__file__) / "../utils/zoom_gstreamer.py"

def run_gmeet( websocket_url, meeting_link):
    """Runs the Google Meet bot."""
    obj = GoogleMeet(meeting_link,websocket_url)
    obj.glogin()
    sleep(5)
    obj.join_meeting()
    obj.record_and_stream(35)
    # Notify the WebSocket once processing is complete
    # await notify_websocket(websocket_url, {"type": "control", "message": "Started Google Meeting Record", "data": ""})


def run_zoom(websocket_url, meeting_link):
    # obj = ZoomMeet(meeting_link=meet_link,ws_link=websocket_url,xvfb_display=display_num,meeting_id="testid")
    display_num = random.randint(2,100)
    # display_num = 44
    script = f'#!/bin/sh \nxvfb-run --listen-tcp --server-num={display_num} --auth-file=/tmp/xvfb.auth -s "-ac -screen 0 1920x1080x24" python -m src.meeting.zoombot {meeting_link} {display_num} {websocket_url} testid'
    # script = f'#!/bin/sh \n python -m src.meeting.zoombot {meeting_link} {0} {websocket_url} testid'
    with open("zoom_launcher.sh",'w') as zoom_launcher:
        zoom_launcher.write(script)


    subprocess.Popen([
        str(Path("zoom_launcher.sh").resolve())
    ])
    # subprocess.Popen([
    #     "env",
    #     f"DISPLAY=:{display_num}",
    #     "xvfb-run",
    #     "--listen-tcp",
    #     "-e /home/lasan/xvfb.log",
    #     f"--server-num={display_num}",
    #     "--auth-file=/tmp/xvfb.auth",
    #     "-w",
    #     "10",
    #     "-s",
    #     "'1280x800x24 -ac -dpi 96 +extension RANDR'",
    #     "python",
    #     "-m",
    #     "src.meeting.zoombot",
    #     f"{meeting_link}",
    #     f"{display_num}",
    #     f"{websocket_url}",
    #     f"testId",
    # ])
    # obj.join_meeting()
    # obj.record_and_stream()
    """Run the Zoom Meet bot."""
    return HTMLResponse("Hello, This is bot to run zoom")


def run_teams( websocket_url, meeting_link):
    """Run the Teams Meet bot."""
    obj = TeamsMeet(meeting_link,websocket_url)
    obj.join_meeting()
    obj.record_and_capture()

    # Notify the WebSocket once processing is complete
    # await notify_websocket(websocket_url, {"type": "control", "message": "Started Teams Meeting Record", "data": ""})

@app.post("/call/gmeet")
async def call_gmeet(meeting: CallMeeting):
    p = Process(target=run_gmeet, args=(WEBSOCKET_URL, meeting.meetingLink))
    p.start()
    return HTMLResponse("Called the Google Meeting bot")


@app.post("/call/teams")
async def call_teams(meeting: CallMeeting):
    p = Process(target=run_teams, args=(WEBSOCKET_URL,meeting.meetingLink))
    p.start()
    return HTMLResponse("Hello, This is bot to login Teams")


@app.post("/call/zoom")
async def call_zoom(meeting: CallMeeting):
    run_zoom(WEBSOCKET_URL, meeting.meetingLink) # not blocking. zoom operates differently
    return HTMLResponse("Hello, This is bot to login Zoom")

