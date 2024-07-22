
(async () =>{
  const stream = document.querySelector("video").srcObject.clone()

  window.stream = stream;
  window.polite = true //politeness settings of webrtc negotiation
  window.chunks = []
  

  let recorder = new mediarecorder(stream,{mimetype:"video/mp4"})
  window.recorder = recorder
  recorder.ondataavailable = (event) => chunks.push(event.data);
  recorder.start();

  window.finaliseanddownloadrec = () =>{
    recorder.stop()
    const blob = new blob(chunks,{type:'video/mp4'})
    var a = document.createelement("a")
    document.body.appendchild(a)
    var url = window.url.createobjecturl(blob)
    a.href = url
    a.download = 'recording.mp4'
    a.click()
    window.url.revokeobjecturl(url)
  }


  const socket = new websocket('ws://localhost:8000/ws');

  socket.onclose = ()=>{
    console.log("websocket closed")
  }

  socket.onopen = () => {
    socket.send(json.stringify({ type: 'join', room: 'room1' }));
  };

  socket.onmessage = async ({data}) => {
    const description = json.parse(data)?.description
    const candidate = json.parse(data)?.candidate
    let makingoffer = false;
    let ignoreoffer = false;
    let issettingremoteanswerpending = false;


    if (json.parse(data)?.connect) {
      // if create signal is recieved from socket, it creates a webrtc obj
      const configuration = {iceservers: [
        {
          urls: "stun:stun.relay.metered.ca:80",
        },
        {
          urls: "turn:global.relay.metered.ca:80",
          username: "2678fb1e408695c7901c6d48",
          credential: "z0t6bane1jdaaxqm",
        },
        {
          urls: "turn:global.relay.metered.ca:80?transport=tcp",
          username: "2678fb1e408695c7901c6d48",
          credential: "z0t6bane1jdaaxqm",
        },
        {
          urls: "turn:global.relay.metered.ca:443",
          username: "2678fb1e408695c7901c6d48",
          credential: "z0t6bane1jdaaxqm",
        },
        {
          urls: "turns:global.relay.metered.ca:443?transport=tcp",
          username: "2678fb1e408695c7901c6d48",
          credential: "z0t6bane1jdaaxqm",
        },
      ],};


      // sets pc to be global variable so that future ice candidates can access it. if another connection is made, this will break the initial connection though
      window.pc = new rtcpeerconnection(configuration);

      // send any ice candidates to the other peer
      pc.onicecandidate = ({candidate}) =>  socket.send(json.stringify({ type: 'candidate', room: 'room1',from:"bot", candidate: candidate }))

      //       
      // let the "negotiationneeded" event trigger offer generation
      pc.onnegotiationneeded = async () => {
        console.log("negotiationneeded")
        try {
          makingoffer = true;
          await pc.setlocaldescription();
          console.log("making offer")
          socket.send(json.stringify({ type: pc.localdescription.type, room: 'room1',from:"bot", description: pc.localdescription }));
        } catch (err) {
          console.error(err);
        } finally {
          makingoffer = false;
        }
      };

      stream.gettracks().foreach(track => pc.addtrack(track, stream));
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
        await pc.setremotedescription(description); // srd rolls back as needed
        issettingremoteanswerpending = false;
        if (description.type == "offer") {
          await pc.setlocaldescription();
          socket.send(json.stringify({ type: pc.localdescription.type, room: 'room1',from:"bot", description: pc.localdescription }));
        }
      } else if (candidate) {
        try {
          await pc.addicecandidate(candidate);
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
