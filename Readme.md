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

### 1. Botserver
1. Create a python virtual environment `virtualenv env`
2. Change shell to virtual environment `source env/bin/activate.sh`
3. Install python dependencies `pip install -r requirements.txt `
4. Navigate to src directory `cd src`
5. Run `fastapi dev app.py`

### 2. Node server
1. Navigate to `src/node_backend`
2. Run `npm i`
3. Run `node server.js`

### 3. React frontend
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
