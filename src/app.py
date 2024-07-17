import uuid
from typing import Union
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

from meeting.gmeet import Gmeet 
from template import templatehtml

# Generate a random UUID
generated_uuid = uuid.uuid4()

# Create room
m_gmeet = Gmeet(generated_uuid)

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/video")
async def read_root():
    return HTMLResponse(templatehtml)

@app.websocket("/ws/text")
async def text_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Request Web Socket")
    # Generate a random UUID
    generated_uuid = uuid.uuid4()
    text_to_send = f"Hello, WebSocket! {generated_uuid}"
    await websocket.send_text(text_to_send)
    print(text_to_send)

    await websocket.close()



@app.websocket("/ws/video")
async def video_endpoint(websocket: WebSocket):
    await websocket.accept()
    await m_gmeet.captureStream(websocket)