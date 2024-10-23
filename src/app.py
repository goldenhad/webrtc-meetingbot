from multiprocessing import Process

from pathlib import Path
import subprocess
import random
from fastapi import FastAPI 
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

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

used_display_nums = []

def run_gmeet( websocket_url, meeting_link):
    """Runs the Google Meet bot."""
    display_num = random.randint(2,100)

    while display_num in used_display_nums:
        display_num = random.randint(2,100)

    script = f'#!/bin/bash \nPULSE_SINK=chrome_sink xvfb-run --listen-tcp --server-num={display_num} --auth-file=/tmp/xvfb.auth -s "-ac -screen 0 1920x1080x24" python -m src.meeting.googlebot "{meeting_link}" "{display_num}" "{websocket_url}" "b1786fdc-1120-41a5-8f7c-3deebdcdd71f"'

    # script = f'#!/bin/sh \n python -m src.meeting.zoombot {meeting_link} {0} {websocket_url} testid'
    with open("google_launcher.sh",'w') as google_launcher:
        google_launcher.write(script)
    # Notify the WebSocket once processing is complete
    subprocess.Popen([
        str(Path("google_launcher.sh").resolve())
    ])

    return HTMLResponse("Hello, This is bot to run google meet")

def run_zoom(websocket_url, meeting_link):
    display_num = random.randint(2,100)
    while display_num in used_display_nums:
        display_num = random.randint(2,100)

    script = f'#!/bin/bash \nPULSE_SINK=chrome_sink xvfb-run --listen-tcp --server-num={display_num} --auth-file=/tmp/xvfb.auth -s "-ac -screen 0 1920x1080x24" python -m src.meeting.zoombot "{meeting_link}" "{display_num}" "{websocket_url}" "b1786fdc-1120-41a5-8f7c-3deebdcdd71f"'
    # script = f'#!/bin/sh \n python -m src.meeting.zoombot {meeting_link} {0} {websocket_url} testid'
    with open("zoom_launcher.sh",'w') as zoom_launcher:
        zoom_launcher.write(script)


    subprocess.Popen([
        str(Path("zoom_launcher.sh").resolve())
    ])

    return HTMLResponse("Hello, This is bot to run zoom")


def run_teams( websocket_url, meeting_link):
    """Run the Teams Meet bot."""
    display_num = random.randint(2,100)

    while display_num in used_display_nums:
        display_num = random.randint(2,100)

    script = f'#!/bin/bash \nPULSE_SINK=chrome_sink xvfb-run --listen-tcp --server-num={display_num} --auth-file=/tmp/xvfb.auth -s "-ac -screen 0 1920x1080x24" python -m src.meeting.teamsbot "{meeting_link}" "{display_num}" "{websocket_url}" "b1786fdc-1120-41a5-8f7c-3deebdcdd71f"'

    # script = f'#!/bin/sh \n python -m src.meeting.zoombot {meeting_link} {0} {websocket_url} testid'
    with open("teams_launcher.sh",'w') as teams_launcher:
        teams_launcher.write(script)

    subprocess.Popen([
        str(Path("teams_launcher.sh").resolve())
    ])
    # Notify the WebSocket once processing is complete
    return HTMLResponse("Hello, This is bot to run teams")
    # await notify_websocket(websocket_url, {"type": "control", "message": "Started Teams Meeting Record", "data": ""})

@app.post("/call/gmeet")
async def call_gmeet(meeting: CallMeeting):
    run_gmeet(WEBSOCKET_URL,meeting.meetingLink)
    return HTMLResponse("Called the Google Meeting bot")


@app.post("/call/teams")
async def call_teams(meeting: CallMeeting):
    run_teams(WEBSOCKET_URL,meeting.meetingLink)
    return HTMLResponse("Hello, This is bot to login Teams")


@app.post("/call/zoom")
async def call_zoom(meeting: CallMeeting):
    run_zoom(WEBSOCKET_URL, meeting.meetingLink) # not blocking. zoom operates differently
    return HTMLResponse("Hello, This is bot to login Zoom")

