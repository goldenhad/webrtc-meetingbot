from datetime import datetime
from typing import Callable, List
from pydantic import UUID4
from websocket import WebSocket
import json

class WebsocketConnection:
    def __init__(self,ws_link: str) -> None:
        self.ws_link: str = ws_link
        self.ws: WebSocket | None = None
        self.analysing_sent: bool = False
        self.room_joined: bool = False
        self.connected: bool = False


    def connect(self, on_message: Callable):
        if self.ws != None and not self.connected:
            self.ws.connect(self.ws_link, on_message = on_message)

    def __ws_send(self,payload: dict):
        if self.ws != None:
            self.ws.send(json.dumps(payload))

    def join_room(self, room_id: str, start_time: datetime, inference_id: UUID4):
        payload = {
            "event": "join-room",
            "data": {"roomId":room_id,"startTime": start_time, "inferenceId": inference_id}
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
                "inferenceId": inference_id,
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

    def close(self):
        if self.ws != None:
            self.ws.close()
            self.connected = False

             

        
