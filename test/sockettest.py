import asyncio
import websockets

async def send_text_via_websocket():
    uri = "ws://localhost:8000/ws/text"  # Replace with your WebSocket server URL
    async with websockets.connect(uri) as websocket:
        # Send text to the WebSocket server
        text_to_send = "Hello, WebSocket!"
        await websocket.send(text_to_send)
        print(f"Sent: {text_to_send}")

        # Wait for a response from the server
        response = await websocket.recv()
        print(f"Received: {response}")

async def send_video_via_websocket():
    uri = "ws://localhost:8000/ws/video"  # Replace with your WebSocket server URL
    async with websockets.connect(uri) as websocket:
        # Send video to the WebSocket server
        video_to_send = "Hello, WebSocket!"
        await websocket.send(video_to_send)
        print(f"Sent: {video_to_send}")

        # Wait for a response from the server
        response = await websocket.recv()
        print(f"Received: {response}")

# Run the coroutine
asyncio.run(send_video_via_websocket())