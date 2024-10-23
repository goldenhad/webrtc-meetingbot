import json
from datetime import datetime
from typing import List

import socketio
from pydantic import UUID4


class WebsocketConnection:
    def __init__(self, ws_link: str, meeting_id) -> None:
        self.ws_link: str = ws_link
        self.sio = socketio.Client()
        self.analysing_sent: bool = False
        self.room_joined: bool = False
        self.connected: bool = False
        self.meeting_id = meeting_id

        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('error', self.on_error)

    def connect(self):
        self.sio.connect(self.ws_link)

    def on_connect(self):
        self.sio.emit('join-room-for-new-bot', self.meeting_id)
        print("Connected to the server from websockemanager")
        self.connected = True

    def on_disconnect(self):
        print("Disconnected from the server")
        self.connected = False

    def on_error(self, error):
        print(f"An error occurred: {error}")

    def __ws_send(self, payload: dict, event: str):
        if self.connected:
            self.sio.emit(event, payload['data'])

    def join_room(self, room_id: str, start_time: datetime, inference_id: UUID4):
        payload = {
            "data": room_id
        }
        if not self.room_joined:
            self.__ws_send(payload, 'join-room')
            self.room_joined = True

    def send_transcription(self, name: str, content: str, start: datetime, end: datetime):
        payload = {
            "data": {
                "name": name,
                "content": content,
                "timeStamps": {
                    "start": start.strftime("%m/%d/%Y %H:%M:%S"),
                    "end": end.strftime("%m/%d/%Y %H:%M:%S")
                }
            }
        }
        self.__ws_send(payload, 'transcription')

    def bot_error(self):
        payload = {
            "data": {}
        }
        self.__ws_send(payload, 'extension-bot-error')

    def send_analysing(self, meeting_id: str, inference_id: UUID4, rtmp_url: str = ""):
        payload = {
            "data": {
                "meetingId": meeting_id,
                "inferenceId": str(inference_id),
                "rtmpUrl": rtmp_url,
            }
        }
        if not self.analysing_sent:
            self.__ws_send(payload, 'analysing')
            self.analysing_sent = True

    def send_participants(self, participants: List[str]):
        payload = {
            "data": participants
        }
        print("Sending participants")
        self.__ws_send(payload, 'participants')

    def send_subject(self, subject: str):
        payload = {
            "data": subject
        }
        self.__ws_send(payload, 'subject')

    def send_processed(self):
        payload = {
            "data": self.meeting_id
        }

        self.__ws_send(payload, 'processed')

