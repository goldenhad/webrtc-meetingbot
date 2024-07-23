
(async () =>{

  const socket = new WebSocket('ws://localhost:7000');
  //webrtc config
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

  //audio setup
  const audioStream = document.querySelector("audio").srcObject.clone()
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
  const pc = new RTCPeerConnection(configuration);

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
    const description = JSON.parse(data)?.description
    const candidate = JSON.parse(data)?.candidate
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

  // observer setup
  const wrapper = document.querySelector('div[data-tid="modern-stage-wrapper"]')
  const config = {subtree: true ,childList:true};
  // Function to be executed when the grandchild element appears
  function handleSpotlight() {
    try {
      console.log("spotlighted")
      const videoNode = document.evaluate("//div[@data-tid='only-videos-wrapper' and (contains(@aria-label, 'pinned') or contains(@aria-label, 'spotlight'))]//video"
        ,document,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null).singleNodeValue
      const vidStream = videoNode.srcObject.clone()

      vidStream.getVideoTracks().forEach(track => {
        window.stream.addTrack(track)
      });


      window.stream.getTracks().forEach(track => {
        const tracks = []
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
        const blob = new Blob(window.chunks,{type:'video/mp4'})
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
  function handleUnspotlight() {
    try {
      console.log("unspotlighted")
      window.recorder.stop()
      pc.getSenders().forEach(sender =>{
        if (sender.track == window.stream.getVideoTracks()[0]) { //only 1 video track is sent. That's how we're sure about this
          pc.removeTrack(sender) 
          console.log("track removed")
        }
      })
      window.stream.removeTrack(window.stream.getVideoTracks()[0])
    } catch (e) {
      console.dir(e)
      console.error(e)
    }
    // Your code here for when the element is removed
  }

  // Callback function to handle mutations
  const mutationCallback = (mutationsList ) => {
    for (let mutation of mutationsList) {
      if (mutation.type === 'childList') {
        for (let addedNode of mutation.addedNodes) {
          if (addedNode.nodeType === Node.ELEMENT_NODE) {
            // Check if the grandchild element with data-cid='stage-participant-spotlighted' exists
            const spottedElement = addedNode.querySelector("[data-cid='stage-participant-spotlighted']");
            if (spottedElement) {
              handleSpotlight();
            }
          }
        } // Check removed nodes
        for (let removedNode of mutation.removedNodes) {
          if (removedNode.nodeType === Node.ELEMENT_NODE) {
            // Check if the removed element or any of its descendants has data-cid='stage-participant-spotlighted'
            if (removedNode.matches("[data-cid='stage-participant-spotlighted']")) {
              handleUnspotlight();
            }
          }
        }
      }
    }
  };


  const observer = new MutationObserver(mutationCallback)
  console.log("Set observer")

  observer.observe(wrapper,config)
  window.observer = observer
  window.socket = socket;

})
