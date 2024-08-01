import asyncio
import json
from datetime import datetime
from typing import List

import websockets
import websockets.sync.client
from pydantic import UUID4


class WebsocketConnection:
    def __init__(self, ws_link: str) -> None:
        self.conn = None
        self.ws_link: str = ws_link
        self.analysing_sent: bool = False
        self.room_joined: bool = False
        self.connected: bool = False

    def connect(self):
        self.conn = websockets.sync.client.connect(self.ws_link)
        self.connected = True
        self.conn.send(json.dumps({
            'event': "join-room",
            'room': "room1"
        }))

    def __ws_send(self, payload: dict):
        if self.conn is not None:
            print("conn isnt none. Sending")
            self.conn.send(json.dumps(payload))
            print("sent")

    def join_room(self, room_id: str, start_time: datetime, inference_id: UUID4):
        payload = {
            "event": "join-room",
            "data": {"roomId": room_id, "startTime": start_time.strftime("%m/%d/%Y %H:%M:%S"), "inferenceId": str(inference_id)}
        }
        if not self.room_joined:
            self.__ws_send(payload)

    def send_transcription(self, name: str, content: str, start: datetime, end: datetime):
        payload = {
            "event": "transcription",
            "data": {"name": name, "content": content, "timeStamps": {
                "start": start.strftime("%m/%d/%Y %H:%M:%S"),
                "end": end.strftime("%m/%d/%Y %H:%M:%S")
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
        print("in send participants")
        self.__ws_send(payload)

    def send_subject(self, subject: str):
        payload = {
            "event": "subject",
            "data": subject
        }
        self.__ws_send(payload)
