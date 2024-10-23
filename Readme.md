## [Meeting Recording Bot Server]
<br />

The bot is working for Google Meeting, Microsoft Teams, Zooms
> Product Roadmap & `Features`:

# Technologies
> Python
> Automation
> Selenium
> WebRTC
> WebSocket

# Technologies

 ## How to run
(the following commands are run on a linux machine from the root folder)

Node - 22 ( This is what I run. It shouldn't really matter as long as its a recent version )
Python - 3.10+

## Setup

### 1. Setting up ubuntu
- Installing gstreamer ````
```
apt-get install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio gstreamer1.0-nice
```
- Installing chrome using wget
```
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
```
- Installing gobject-introspection
```
sudo apt-get install libgirepository1.0-dev
```
- Installing python-development packages
```
sudo apt install libcairo2-dev pkg-config python3-dev
```
- Setting up a pulse audio sink ( install pulseaudio if command not found )
```
pactl load-module module-null-sink sink_name=chrome_sink sink_properties=device.description="Chrome_Sink"
```
*If you get an error like 'Access is denied' or something, You might want to add current user to pulse-access group*
- Installing xvfb for headless mode
```
sudo apt install xvfb
```
### 2. Setting up project for deployment

- Clone project. Switch to `v2` branch. 
- Navigate to `.env` folder and comment out `DEV = 'True'`. Setting ` DEV = 'False'` won't be enough. 
- Create virtual python environment 
```
virtualenv venv
```
- Switch to virtual environment
```
source venv/bin/activate
```
- Navigate to project root
- Install requirements. 
```
pip install -r requirements.txt
```
- Give executable permissions to launchers.
```
chmod +x *.sh
```
### 3. Running project

- Running fastapi server. Must be run from project root. Otherwise, launchers are recreated and executable permissions must be re-issued. We are using development mode for the demo
```
fastapi dev src/app.py
```
*Node server must be running on port 7000 for the bots to function properly*
- Run bots from either calling the http endpoints or navigating to `http://localhost:8000/docs` interface

### 4. Node server
1. Navigate to `src/node_backend`
2. Run `npm i`
3. Run `node server.js`

### 5. React frontend
1. Navigate to `src/frontend`
2. Run `npm i`
3. Run `npm start`
4. Your default browser should automatically open. If it doesn't, go to `http://localhost:3000`

###  Calling a bot
- You can use whatever tool you like to issue a POST request to `http://localhost:8000/call/gmeet` for google meet or `http://localhost:8000/call/teams` for teams or `http://localhost:8000/call/zoom` for zoom.
- Make sure to send the meeting link in the body as below:
```json
{meetingLink: ""}
```

- You can use the graphical tool at `http://localhost:8000/docs` If you are familiar with the swagger API docs
