from multiprocessing import Process
from time import sleep

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



def run_gmeet( websocket_url, meeting_link):
    """Runs the Google Meet bot."""
    obj = GoogleMeet(meeting_link,websocket_url)
    obj.glogin()
    sleep(5)
    obj.join_meeting()
    obj.record_and_stream(35)
    # Notify the WebSocket once processing is complete
    # await notify_websocket(websocket_url, {"type": "control", "message": "Started Google Meeting Record", "data": ""})


def run_zoom(meet_link, websocket_url, meeting_link):
    """Run the Zoom Meet bot."""


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
    return HTMLResponse("Hello, This is bot to login Zoom")

