#!/bin/sh 
xvfb-run --listen-tcp --server-num=70 --auth-file=/tmp/xvfb.auth -s "-ac -screen 0 1920x1080x24" python -m src.meeting.zoombot https://us04web.zoom.us/j/75676660585?pwd=6vrRIbsCPR3jfdiKPvO8CvD1bD4aNX.1 70 ws://localhost:7000 testid