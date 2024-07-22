import subprocess
ffmpeg_command = [
    'ffmpeg',
    '-f', 'x11grab',
    '-i', ':0',
    '-framerate', '24',  # or whatever frame rate you want
    '-tune', 'zerolatency',  # or whatever frame rate you want
    '-preset', 'ultrafast',  # or whatever frame rate you want
    '-video_size', f"{640}x{640}",
    "-vcodec","libx264",
    "-b","900k",
    '-f', 'x11grab',  # Format for RTMP
    "udp://127.0.0.1:5004"
]

subprocess.Popen(ffmpeg_command)
