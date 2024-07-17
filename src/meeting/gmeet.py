
import subprocess
import asyncio
import time
import websockets
from fastapi import WebSocket,WebSocketDisconnect

class Gmeet:
    def __init__(self,uuid):
        self.uuid = uuid

    async def captureStream(self,websocket: WebSocket):
        try:
            # Command to capture video and audio using FFmpeg and output as MPEG-TS
            command = [
                'ffmpeg',
                '-f', 'gdigrab',       # Grab device
                '-framerate', '30',    # Frame rate
                '-i', 'desktop',       # Capture the entire desktop
                '-video_size', f"{100}x{200}",  # Video size
                '-offset_x', str(0),
                '-offset_y', str(0),
                '-f', 'dshow',         # DirectShow audio capture
                # '-i', 'audio="Microphone (Realtek(R) Audio)"',  # Specify your audio device name
                '-c:v', 'libx264',     # Video codec
                '-pix_fmt', 'yuv420p', # Pixel format compatible with most browsers
                '-preset', 'veryfast', # Faster preset for live streaming
                '-c:a', 'aac',         # Audio codec
                '-b:v', '1M',          # Video bitrate
                '-b:a', '128k',        # Audio bitrate
                '-muxdelay', '0.1',    # Reduce delay
                '-f', 'mpegts',        # Output format
                'pipe:1'               # Output to stdout
            ]
            
            #./ffmpeg.exe -f gdigrab -framerate 30 -video_size 100x200 -offset_x 0 -offset_y 0 -i desktop -f dshow -i audio="Microphone (Realtek(R) Audio)" -c:v libx264 -pix_fmt yuv420p -preset veryfast -c:a aac -b:v 1M -b:a 128k -muxdelay 0.1 -f mpegts pipe:1
            
            # Start FFmpeg process
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8)
            print(process) 
            
            while True:
                data = process.stdout.read(8192)
                print(len(data)) 
                if not data:
                    break
                await websocket.send_bytes(data)
                # asyncio.wait(5)
                # time.sleep(5)
        

        except WebSocketDisconnect:
            process.kill()
            print("Client disconnected")


    async def forwardStream(self):
        print("start streaming")
        RMTP_SERVER_URL = "rtmp://rtmp-live-ingest-us-east-1-universe.dacast.com/transmuxv1"
        STREAM_KEY = "59e6e0f8-ac9a-d328-6ff6-dd4e9998f834?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdHJlYW1JZCI6IjU5ZTZlMGY4LWFjOWEtZDMyOC02ZmY2LWRkNGU5OTk4ZjgzNCIsInR5cGUiOiJwdWJsaXNoIn0.bljB-Pzrr9LfcIxxhzvymNqtfRUykgNjkxbLEapE5m0"
        # Command to capture video and audio using FFmpeg and output as MPEG-TS
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'gdigrab',
            '-framerate', '30',  # or whatever frame rate you want
            '-video_size', f"{200}x{200}",
            # '-i', f"Axacraft | Digital Transformation special forces strategy & execution team. - Google Chrome",  # Change window title as needed
            '-i', f"desktop",  # Change window title as needed
            '-offset_x', str(0),
            '-offset_y', str(0),
            '-vf', 'crop=trunc(iw/2)*2:ih',  # Ensure width is divisible by 2
            '-vcodec', 'libx264',  # Video codec set to H.264
            '-pix_fmt', 'yuv420p',  # Pixel format compatible with most browsers
            '-preset', 'veryfast',  # Faster preset for live streaming
            '-f', 'flv',  # Format for RTMP
            f'{RMTP_SERVER_URL}/{STREAM_KEY}'  # Your RTMP server URL and stream key
        ]

        
        
        #./ffmpeg.exe -f gdigrab -framerate 30 -video_size 100x200 -offset_x 0 -offset_y 0 -i desktop -f dshow -i audio="Microphone (Realtek(R) Audio)" -c:v libx264 -pix_fmt yuv420p -preset veryfast -c:a aac -b:v 1M -b:a 128k -muxdelay 0.1 -f mpegts pipe:1
        
        # Start recording
        subprocess.Popen(ffmpeg_command)
        # Keep streaming; stop with a condition or user input
        try:
            while True:
                asyncio.wait(1)  # Keep the stream alive until an interrupt
        except KeyboardInterrupt:
            print("Streaming stopped.")

        print(f"Streaming finished ... ")




