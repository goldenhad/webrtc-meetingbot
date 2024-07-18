#import uuid
from multiprocessing import Process
import json
#import asyncio
#from time import sleep
#from typing import Union
from time import sleep
from typing import List, Dict
import websockets
from fastapi import FastAPI, WebSocket, BackgroundTasks, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from src.meeting.googlebot import JoinGoogleMeet
#from src.template import templatehtml

from src.utils.constants import GOOGLE_MEETING_LINK
from src.websocketmanager import ConnectionManager
# Generate a random UUID
# generated_uuid = uuid.uuid4()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # can alter with time
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
WsManager = ConnectionManager()


def run_gmeet(meet_link,websocket_url):
    obj = JoinGoogleMeet()
    obj.Glogin()
    sleep(20)
    obj.turnOffMicCam(meet_link)
    obj.AskToJoin()
    obj.Record(35)
    # Notify the WebSocket once processing is complete
    # await notify_websocket(websocket_url, {"type":"control","message": "Started Google Meeting Record", "data": ""})


async def run_teams(meet_link,websocket_url):
    obj = JoinGoogleMeet()
    
    # Notify the WebSocket once processing is complete
    await notify_websocket(websocket_url, {"type":"control","message": "Started Teams Meeting Record", "data": ""})

# Function to notify the WebSocket
async def notify_websocket(websocket_url: str, data: dict):
    async with websockets.connect(websocket_url) as websocket:
        await websocket.send(str(data))
        response = await websocket.recv()
        print(f"Received response from websocket: {response}")

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/call/gmeet")
async def call_gmeet( background_tasks: BackgroundTasks):
    # Add the processing task to the background
    websocket_url = "ws://localhost:3000/websocket"  # Replace with your WebSocket URL
    p = Process(target=run_gmeet,args=(GOOGLE_MEETING_LINK,websocket_url))
    p.start()
    print("finished background tast")
    return HTMLResponse("Called the Google Meeting bot")

@app.get("/call/teams")
async def call_teams():

    return HTMLResponse("Hello, This is bot to login teams")

@app.get("/call/zoom")
async def call_zoom():
    return HTMLResponse("Hello, This is bot to login zoom")


# WebSocket endpoint to handle incoming WebSocket connections
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await WsManager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            if data_json["type"] == "join":
                await WsManager.broadcast(json.dumps(data_json))
            else:
                await WsManager.broadcast_except(websocket,json.dumps(data_json))
    except WebSocketDisconnect:
        print("WebSocket connection closed")


@app.websocket("/ws/video")
async def video_endpoint(websocket: WebSocket):
    await websocket.accept()
    # await m_gmeet.captureStream(websocket)
