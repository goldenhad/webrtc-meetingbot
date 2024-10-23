const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');

const app = express();
app.use(cors());
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*',
  }
});

io.on('connection', (socket) => {
  console.log('A user connected:', socket.id);

  socket.on('join-room-for-new-bot', (room) => {
    socket.join(room);
    socket.joined_room = room
    console.log(`User ${socket.id} joined room ${room}`);
  });

  // Handle webrtc events
  const webrtcEvents = ['livestream', 'connect', 'offer', 'answer', 'candidate'];
  webrtcEvents.forEach(event => {
    socket.on(event, (data) => {
      console.log(`${event} event received`);
      socket.to(socket.joined_room).emit(event, data);
      console.log("sent data to bot")
    });
  });

  socket.on('test',(data)=>{
    console.log(socket.rooms)
    socket.to(socket.joined_room).emit('test', data);
    console.log('got test')
  })

  socket.on('select-subject', (data) => {
    console.log('select subject event received');
    socket.to(socket.joined_room).emit('select-subject', data);
    console.log("sent to room")
  });

  socket.on('transcription', (data) => {
    console.log('transcription event received');
    console.log(data);
  });

  socket.on('extension-bot-error', () => {
    console.log('extension-bot-error event received');
  });

  socket.on('analysing', (data) => {
    console.log('analysing event received');
    console.log(data);
  });

  socket.on('participants', (data) => {
    console.log('participant event received');
    console.log(data);
  });

  socket.on('subject', (data) => {
    console.log('subject event received');
    console.log(data);
  });

  socket.on('processed', (data) => {
    console.log('processed event received');
    console.log(data);
  });

  socket.on('disconnect', () => {
    console.log(`User ${socket.id} disconnected`);
  });
});

const PORT = 7000;
server.listen(PORT, () => {
  console.log(`Signaling server running on port ${PORT}`);
});
