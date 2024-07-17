templatehtml = """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Video Stream</title>
</head>
<body>
    <h1>WebSocket Video Stream</h1>
    <video id="videoPlayer" autoplay></video>

    <script>
        const video = document.getElementById('videoPlayer');
        const websocket = new WebSocket("ws://localhost:8000/ws/video");

        websocket.onmessage = function(event) {
            const blob = new Blob([event.data], { type: 'video/mp4' });
            const url = URL.createObjectURL(blob);
            video.src = url;
        };

        websocket.onclose = function(event) {
            console.log("WebSocket connection closed");
        };
    </script>
</body>
</html>
"""