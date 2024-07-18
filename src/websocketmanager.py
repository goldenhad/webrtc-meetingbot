from fastapi import WebSocket 
from typing import List

from fastapi.websockets import WebSocketState

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Broadcasts message to self websocket
        """
        if websocket.state == WebSocketState.CONNECTED or websocket.state == WebSocketState.CONNECTED:
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        """
        Broadcasts message to all websockets
        """
        for connection in self.active_connections:
            if connection.state == WebSocketState.CONNECTED or connection.state == WebSocketState.CONNECTED:
                await connection.send_text(message)

    async def broadcast_except(self,websocket:WebSocket, message: str):
        """
        Broadcasts message to all websockets except one websocket
        """
        print("send message to broadcast")
        print(message)
        for connection in self.active_connections:
            if websocket != connection:
                if connection.application_state == WebSocketState.CONNECTED or connection.application_state == WebSocketState.CONNECTED:
                    print('send to conenction')
                    await connection.send_text(message)

