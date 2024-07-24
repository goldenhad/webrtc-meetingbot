(()=>{
  // Define the WebsocketConnection class
  class WebsocketConnection {
    constructor(wsLink, options) {
      console.log(options)
      this.wsLink = wsLink || "";
      this.ws = options && options.websocket || null;
      this.analysingSent = false;
      this.roomJoined = options && options.roomJoined || false;
      this.connected = options && options.websocket.readyState == WebSocket.OPEN || false;

    }

    connect(onMessage) {
      if (this.ws === null && !this.connected) {
        this.ws = new WebSocket(this.wsLink);

        this.ws.onmessage = (event) => {
          if (onMessage) {
            onMessage(event);
          }
        };

        this.ws.onopen = () => {
          this.connected = true;
        };

        this.ws.onclose = () => {
          this.connected = false;
          this.ws = null;
        };
      } else if (this.ws != null && this.connected) {
        const oldOnmessage = ws.onmessage
        const oldOnopen = ws.onopen
        const oldOnclose = ws.onclose
        this.ws.onmessage = (event) =>{
          oldOnmessage(event)
          onMessage(event)
        }
        this.ws.onopen = () => {
          oldOnopen()
          this.connected = true;
        };

        this.ws.onclose = () => {
          oldOnclose()
          this.connected = false;
          this.ws = null;
        };

      }
    }

    _wsSend(payload) {
      if (this.ws !== null) {
        this.ws.send(JSON.stringify(payload));
      }
    }

    joinRoom(roomId, startTime, inferenceId) {
      const payload = {
        event: "join-room",
        data: {
          roomId: roomId,
          startTime: startTime.toISOString(), // Converting datetime to ISO string
          inferenceId: inferenceId
        }
      };
      if (!this.roomJoined) {
        this._wsSend(payload);
        this.roomJoined = true;
      }
    }

    sendTranscription(name, content, start, end) {
      const payload = {
        event: "transcription",
        data: {
          name: name,
          content: content,
          timeStamps: {
            start: start, 
            end: end        
          }
        }
      };
      this._wsSend(payload);
    }

    botError() {
      const payload = {
        event: "extension-bot-error"
      };
      this._wsSend(payload);
    }

    sendAnalysing(meetingId, inferenceId, rtmpUrl = "") {
      const payload = {
        event: "analysing",
        data: {
          meetingId: meetingId,
          inferenceId: inferenceId,
          rtmpUrl: rtmpUrl
        }
      };
      if (!this.analysingSent) {
        this._wsSend(payload);
        this.analysingSent = true;
      }
    }

    sendParticipants(participants) {
      const payload = {
        event: "participants",
        data: participants
      };
      this._wsSend(payload);
    }

    sendSubject(subject) {
      const payload = {
        event: "subject",
        data: subject
      };
      this._wsSend(payload);
    }

    close() {
      if (this.ws !== null) {
        this.ws.close();
        this.connected = false;
        this.ws = null;
      }
    }
  }

  // Attach the WebsocketConnection class to the window object
  window.WebsocketConnection = WebsocketConnection;
})();
