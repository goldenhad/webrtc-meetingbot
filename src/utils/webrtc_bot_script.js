const video = arguments[0];
const stream = video.captureStream();
window.stream = stream;

let chunks = []

let recorder = new MediaRecorder(stream)
recorder.ondataavailable = (event) => chunks.push(event.data);
recorder.start();


const socket = new WebSocket('ws://localhost:8000/ws');

socket.onopen = () => {
  socket.send(JSON.stringify({ type: 'join', room: 'room1' }));
};
const polite = false
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

const waitForSocketOpen = (socket) => {
  return new Promise((resolve, reject) => {
    if (socket.readyState === WebSocket.OPEN) {
      resolve();
    } else {
      socket.addEventListener('open', resolve, { once: true });
      socket.addEventListener('error', reject, { once: true });
    }
  });
};

const pc = new RTCPeerConnection(configuration);
let makingoffer = false;
let ignoreoffer = false;
let issettingremoteanswerpending = false;

// send any ice candidates to the other peer
pc.onicecandidate = ({candidate}) =>  socket.send(JSON.stringify({ type: 'candidate', room: 'room1',from:"bot", candidate: candidate }))
//       
// let the "negotiationneeded" event trigger offer generation
pc.onnegotiationneeded = async () => {
  console.log("negotiationneeded")
  try {
    makingoffer = true;
    await pc.setLocalDescription();
    console.log("making offer")
    await waitForSocketOpen(socket)
    socket.send(JSON.stringify({ type: pc.localDescription.type, room: 'room1',from:"bot", description: pc.localDescription }));
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
        socket.send(JSON.stringify({ type: pc.localDescription.type, room: 'room1',from:"bot", description: pc.localDescription }));
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
pc.addEventListener("connectionstatechange",()=>{
  if (pc.connectionState == "connected"){

    console.log("track added to peerconnection")
  }
  if (pc.connectionState == "disconnected"||pc.connectionState == "closed"){

    console.log("started recording")
    const blob = new Blob(chunks,{type:'video/webm'})
    var a = document.createElement("a")
    document.body.appendChild(a)
    var url = window.URL.createObjectURL(blob)
    a.href = url
    a.download = 'recording.mp4'
    a.click()
    window.URL.revokeObjectURL(url)
  }
})
stream.getTracks().forEach(track => pc.addTrack(track, stream));

console.log("finished execution of script")
