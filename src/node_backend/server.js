const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const cors = require('cors');

const app = express();
app.use(cors())
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

let rooms = {};

wss.on('connection', (ws) => {
  ws.on('message', (message) => {
    const data = JSON.parse(message);
    switch (data.event) {
      case 'join-room':
        if (!rooms[data.room]) {
          rooms[data.room] = [];
        }
        rooms[data.room].push(ws); // add websocket to room
        console.log("joined")
        ws.room = data.room;
        break;
      
      // webrtc events
      case "livestream":
      case 'connect':
      case 'offer':
      case 'answer':
      case 'candidate':
        // Broadcast to room without sending to self
        if (rooms[data.room]) {
          rooms[data.room].forEach(client => {
            if (client !== ws) {
              //console.log(data)
              client.send(JSON.stringify(data));
            }
          });
        }
        break;

      case 'select-subject':
        console.log("subject event recieved")
          rooms['room1'].forEach(client => {
            if (client !== ws) {
              console.log("send subject event")
              client.send(JSON.stringify(data));
            }
          });
        break;
      case 'transcription':
        console.log("transcription event recieved")
        console.log(data.data)
        break;
      case 'extension-bot-error':
        console.log("extension-bot-error event recieved")
        break;
      case 'analysing':
        console.log("analysing event recieved")
        console.log(data.data)
        break;
      case 'participant':
        console.log("participant event recieved")
        console.log(data.data)
        break;
      case 'subject':
        console.log("subject event recieved")
        console.log(data.data)
        break;
        break;
      case 'processed':
        console.log("processed event recieved")
        console.log(data.data)
        break;

    }
  });

  ws.on('close', () => {
    if (ws.room) {
      rooms[ws.room] = rooms[ws.room].filter(client => client !== ws);
      if (rooms[ws.room].length === 0) {
        delete rooms[ws.room];
      }
    }
  });
});

const PORT = 7000;
server.listen(PORT, () => {
  console.log(`Signaling server running on port ${PORT}`);
});
