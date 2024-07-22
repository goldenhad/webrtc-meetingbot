
(async () =>{

  //console.log("ran this")

  //const vidStream = document.evaluate(
  //  "//*[@data-cid='stage-participant-spotlighted']/ancestor::div[@data-cid='calling-participant-stream']//div[@data-tid='video-stream']//video",
  //  document,
  //  null,
  //  XPathResult.ORDERED_NODE_SNAPSHOT_TYPE
  //).snapshotItem(0)


  
  // TODO: Transition to mutation observer. Don't look for elments in python
  //console.log(vid_element)
  const vidStream = arguments[0].srcObject.clone()

  console.log("got vidstream")
  console.log(vidStream)

  const audioStream = document.querySelector("audio").srcObject.clone()

  //setting up window.stream object to stream 
  const stream = new MediaStream()

  vidStream.getVideoTracks().forEach(track => {
    window.stream.addTrack(track)
  });
  audioStream.getAudioTracks().forEach(track => {
    window.stream.addTrack(track)
  });


  window.polite = true //politeness settings of webrtc negotiation
  window.chunks = []
  

  let recorder = new MediaRecorder(stream,{mimeType:"video/mp4"})
  window.recorder = recorder
  recorder.ondataavailable = (event) => chunks.push(event.data);
  recorder.start();

  window.finaliseAndDownloadRec = () =>{
    recorder.stop()
    const blob = new Blob(chunks,{type:'video/mp4'})
    var a = document.createElement("a")
    document.body.appendChild(a)
    var url = window.URL.createObjectURL(blob)
    a.href = url
    a.download = 'recording.mp4'
    a.click()
    window.URL.revokeObjectURL(url)
  }


  const socket = new WebSocket('ws://localhost:7000');

  socket.onclose = ()=>{
    console.log("websocket closed")
  }

  socket.onopen = () => {
    socket.send(JSON.stringify({ event: 'join-room', room: 'room1' }));
  };

  socket.onmessage = async ({data}) => {
    const description = JSON.parse(data)?.description
    const candidate = JSON.parse(data)?.candidate
    let makingoffer = false;
    let ignoreoffer = false;
    let issettingremoteanswerpending = false;


    if (JSON.parse(data)?.event == "connect") {
      // if create signal is recieved from socket, it creates a webrtc obj
      const configuration = {iceServers: [
        {
          urls: "stun:stun.relay.metered.ca:80",
        },
        {
          urls: "turn:global.relay.metered.ca:80",
          username: "2678fb1e408695c7901c6d48",
          credential: "z0t6BANE1JdAAXQm",
        },
        {
          urls: "turn:global.relay.metered.ca:80?transport=tcp",
          username: "2678fb1e408695c7901c6d48",
          credential: "z0t6BANE1JdAAXQm",
        },
        {
          urls: "turn:global.relay.metered.ca:443",
          username: "2678fb1e408695c7901c6d48",
          credential: "z0t6BANE1JdAAXQm",
        },
        {
          urls: "turns:global.relay.metered.ca:443?transport=tcp",
          username: "2678fb1e408695c7901c6d48",
          credential: "z0t6BANE1JdAAXQm",
        },
      ],};

      // Perfect WebRTC peer negotiation pattern
      // https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Perfect_negotiation

      // sets pc to be global variable so that future ice candidates can access it. If another connection is made, this will break the initial connection though
      window.pc = new RTCPeerConnection(configuration);

      // send any ice candidates to the other peer
      pc.onicecandidate = ({candidate}) =>  socket.send(JSON.stringify({ event: 'candidate', room: 'room1',from:"bot", candidate: candidate }))

      //       
      // let the "negotiationneeded" event trigger offer generation
      pc.onnegotiationneeded = async () => {
        console.log("negotiationneeded")
        try {
          makingoffer = true;
          await pc.setLocalDescription();
          console.log("making offer")
          socket.send(JSON.stringify({ event: pc.localDescription.type, room: 'room1',from:"bot", description: pc.localDescription }));
        } catch (err) {
          console.error(err);
        } finally {
          makingoffer = false;
        }
      };


      stream.getTracks().forEach(track => pc.addTrack(track, stream));
    }
    try {
      if (description) {
        // an offer may come in while we are busy processing srd(answer).
        // in this case, we will be in "stable" by the ime the offer is processed
        // so it is safe to chain it on our operations chain now.
        const readyforoffer =
          !makingoffer &&
          (pc.signalingstate == "stable" || issettingremoteanswerpending);
        const offercollision = description.type == "offer" && !readyforoffer;

        ignoreoffer = !polite && offercollision;
        if (ignoreoffer) {
          return;
        }
        issettingremoteanswerpending = description.type == "answer";
        await pc.setRemoteDescription(description); // srd rolls back as needed
        issettingremoteanswerpending = false;
        if (description.type == "offer") {
          await pc.setLocalDescription();
          socket.send(JSON.stringify({ event: pc.localDescription.type, room: 'room1',from:"bot", description: pc.localDescription }));
        }
      } else if (candidate) {
        try {
          await pc.addIceCandidate(candidate);
        } catch (err) {
          if (!ignoreoffer) throw err; // suppress ignored offer's candidates
        }
      }
    } catch (err) {
      console.error(err);
    }   //};
  }
  window.socket = socket;

})()
