import asyncio
from datetime import datetime
from typing import Callable, List
from pydantic import UUID4
import websockets
import json

class WebsocketConnection:
    def __init__(self,ws_link: str) -> None:
        self.ws_link: str = ws_link
        self.analysing_sent: bool = False
        self.room_joined: bool = False
        self.connected: bool = False

    async def connect(self):
        self.conn = await websockets.connect(self.ws_link)
        await self.conn.send(json.dumps({
            'event':"join-room",
            'room':"room1"   
        }))

    def __ws_send(self,payload: dict):
        if self.conn != None:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.conn.send(json.dumps(payload)))

            
    def join_room(self, room_id: str, start_time: datetime, inference_id: UUID4):
        payload = {
            "event": "join-room",
            "data": {"roomId":room_id,"startTime": start_time, "inferenceId": str(inference_id)}
        }
        if not self.room_joined:
            self.__ws_send(payload)

    def send_transcription(self, name: str, content: str, start: datetime, end: datetime):
        payload = {
            "event": "transcription",
            "data": {"name":name,"content": content, "timeStamps": {
                "start": start,
                "end": end
            }}
        }
        self.__ws_send(payload)

    def bot_error(self):
        payload = {
            "event": "extension-bot-error"
        }
        self.__ws_send(payload)


    def send_analysing(self, meeting_id: str, inference_id: UUID4, rtmp_url: str = ""):
        payload = {
            "event": "analysing",
            "data": {
                "meetingId": meeting_id,
                "inferenceId": str(inference_id),
                "rtmpUrl": rtmp_url,
            }
        }
        if not self.analysing_sent:
            self.__ws_send(payload)
            self.analysing_sent = True

    def send_participants(self, participants: List[str]):
        payload = {
            "event": "participants",
            "data": participants
        }
        self.__ws_send(payload)

    def send_subject(self, subject: str):
        payload = {
            "event": "subject",
            "data": subject
        }
        self.__ws_send(payload)


             

        
