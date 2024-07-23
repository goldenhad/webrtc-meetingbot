
(async () =>{

  let socket = new WebSocket('ws://localhost:7000');
  //webrtc config
  let configuration = {iceServers: [
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

  //audio setup
  let audioStream = document.querySelector("audio").srcObject.clone()
  window.stream = new MediaStream()
  audioStream.getAudioTracks().forEach(track => {
    window.stream.addTrack(track)
  });


  window.polite = true //politeness settings of webrtc negotiation
  window.chunks = []
  //window.videoSender = null

  socket.onclose = ()=>{
    console.log("websocket closed")
  }

  socket.onopen = () => {
    socket.send(JSON.stringify({ event: 'join-room', room: 'room1' }));
  };

  let makingoffer = false;
  let ignoreoffer = false;
  let issettingremoteanswerpending = false;

  // Perfect WebRTC peer negotiation pattern
  // https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Perfect_negotiation

  // sets pc to be global variable so that future ice candidates can access it. If another connection is made, this will break the initial connection though
  let pc = new RTCPeerConnection(configuration);

  // send any ice candidates to the other peer
  pc.onicecandidate = ({candidate}) =>  socket.send(JSON.stringify({ event: 'candidate', room: 'room1',from:"bot", candidate: candidate }))

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

  socket.onmessage = async ({data}) => {
    let description = JSON.parse(data)?.description
    let candidate = JSON.parse(data)?.candidate
    try {
      if (description) {
        // an offer may come in while we are busy processing srd(answer).
        // in this case, we will be in "stable" by the ime the offer is processed
        // so it is safe to chain it on our operations chain now.
        let readyforoffer =
          !makingoffer &&
          (pc.signalingstate == "stable" || issettingremoteanswerpending);
        let offercollision = description.type == "offer" && !readyforoffer;

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
  function switchStream(videoElement){
    try {
      window.recorder.stop()
      pc.getSenders().forEach(sender =>{
        if (sender.track == window.stream.getVideoTracks()[0]) { //only 1 video track is sent. That's how we're sure about this
          pc.removeTrack(sender) 
        }
      })
      window.stream.removeTrack(window.stream.getVideoTracks()[0])
    } catch (e) {
      console.dir(e)
      console.error(e)
    }
    try {
      console.log("spotlighted")
      let vidStream = videoElement.srcObject.clone()

      vidStream.getVideoTracks().forEach(track => {
        window.stream.addTrack(track)
      });


      window.stream.getTracks().forEach(track => {
        let tracks = []
        pc.getSenders().forEach(element => {
          tracks.push(element.track) 
        });

        if (!tracks.includes(track)) {
          pc.addTrack(track, window.stream)
        }
      });
      console.log("Finished adding tracks to pc")

      //recorder setup
      let recorder = new MediaRecorder(window.stream,{mimeType:"video/mp4"})
      console.log('created mediarecorder')
      window.recorder = recorder
      window.recorder.onstop = (e) =>{
        console.log("chunks rec stop",window.chunks)
        console.log("recording stopped")
        let blob = new Blob(window.chunks,{type:'video/mp4'})
        var a = document.createElement("a")
        document.body.appendChild(a)
        var url = window.URL.createObjectURL(blob)
        a.href = url
        a.download = 'recording.mp4'
        a.click()
        window.URL.revokeObjectURL(url)
        window.chunks = []
      }
      window.recorder.ondataavailable = (event) => {
        window.chunks.push(event.data)
      };
      window.recorder.start(1000);
      console.log("Recording started")

    } catch (e) {
      console.warn("handleSpotlightError: ",e)  
    }



  }
  let switchTimer;
  const delayedSwitch = () =>{
    if (switchTimer != null && switchTimer != undefined) {
      clearTimeout(switchTimer)
      
    }
    switchTimer = setTimeout(() => {
      let videoElement = document.querySelector("div[data-cid='calling-participant-stream'] video")
      console.dir(videoElement)
      if (videoElement) {
        switchStream(videoElement)
      }
    }, 1000);
  }

  let observerCallback = (mutationsList ) => {
    for (let mutation of mutationsList) {
      if (mutation.type === 'childList') {

        for (let addedNode of mutation.addedNodes) {
          if (addedNode.nodeType === Node.ELEMENT_NODE) {
            if (addedNode.querySelector('[data-cid="stage-participant-pinned"]')) {
              console.log("added pinned participant") 
              delayedSwitch()
            }
            if (addedNode.matches('[data-cid="calling-participant-stream"]' )) { // Is the added node, the node we want to be seen?

              console.log("added calling participant stream") 
              delayedSwitch()
              // waiting 0.5s till video element becomes available


            }
          }
        } // Check removed nodes
        for (let removedNode of mutation.removedNodes){
          if (removedNode.nodeType === Node.ELEMENT_NODE) {
            if (removedNode.matches('[data-cid="stage-participant-pinned"]') 
              || removedNode.matches('[data-cid="calling-participant-stream"]'
              || removedNode.matches('[data-tid=""]')
              )) {
              console.log("removed pinned participant / stage") 
              delayedSwitch()
            }
          }
        }
        //
      }
    }
  }

  // observer setup
  let wrapper = document.querySelector('div[data-testid="stage-segment-wrapper"]')
  let config = {subtree: true ,childList:true, attributes:true,attributeFilter:["data-acc-id"]};

  let observer = new MutationObserver(observerCallback)
  console.log("Set observer")

  observer.observe(wrapper,config)
  window.observer = observer
  window.socket = socket;

})()
