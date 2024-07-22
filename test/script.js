(function() { 
  //overide the browser's default RTCPeerConnection. 
  var origPeerConnection = window.RTCPeerConnection || window.webkitRTCPeerConnection || window.mozRTCPeerConnection;
  window.streams = []
  //make sure it is supported
  console.log("here we go")
  if (origPeerConnection) {
    console.log("Still supported")
    //our own RTCPeerConnection
    var newPeerConnection = function(config, constraints) {
      console.log('PeerConnection created with config', config);
      //proxy the orginal peer connection
      var pc = new origPeerConnection(config, constraints);
      //store the old addStream
      var oldAddTrack = pc.addTrack;
      var old_ontrack = pc.ontrack;

      //addStream is called when a local stream is added. 
      //arguments[0] is a local media stream
      pc.addTrack = function() {
        console.log("our add stream called!")
        //our mediaStream object
        console.dir(arguments[0])
        return oldAddTrack.apply(this, arguments);
      }

      //ontrack is called when a remote track is added.
      //the media stream(s) are located in event.streams
      pc.ontrack = function(event) {
        console.log("ontrack got a track")
        console.dir(event);
        streams.push(event.streams)
        return old_ontrack.apply(this, arguments);
      }
      window.ourPC = pc;

      return pc; 
    };

    ['RTCPeerConnection', 'webkitRTCPeerConnection', 'mozRTCPeerConnection'].forEach(function(obj) {
      // Override objects if they exist in the window object
      if (window.hasOwnProperty(obj)) {
        window[obj] = newPeerConnection;
        // Copy the static methods
        Object.keys(origPeerConnection).forEach(function(x){
          window[obj][x] = origPeerConnection[x];
        })
        window[obj].prototype = origPeerConnection.prototype;
      }
    });
  }

})();
