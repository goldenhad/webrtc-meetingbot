(()=>{
  const wsManager = new window.WebsocketConnection("",{websocket:window.socket,roomJoined:true})
  let lastSentTranscriptionTime = Date.now()
  const targetNode = document.querySelector('div[data-tid="closed-captions-renderer"]');
  // Callback function to execute when mutations are observed
  const callback = function(mutationsList) {
    for (const mutation of mutationsList) {
      if (mutation.type === 'childList') {
        for (const addedNode of mutation.addedNodes) {
          if (addedNode.nodeType === Node.ELEMENT_NODE && addedNode.querySelector('li[class*="ui-chat__item"]')) {
            try {
              const previousNode = addedNode.previousSibling
              // Get the descendant span with class containing "ui-chat__message__author"
              const authorSpan = previousNode.querySelector('span[class*="ui-chat__message__author"]');
              const author = authorSpan ? authorSpan.textContent : null;

              // Get the span with data-tid="closed-caption-text"
              const contentSpan = previousNode.querySelector('span[data-tid="closed-caption-text"]');
              const content = contentSpan ? contentSpan.textContent : null;

              if (author && content) {
                // Save the author and content to variables or handle them as needed

                //console.log(content)
                wsManager.sendTranscription(
                  author,
                  content,
                  lastSentTranscriptionTime,
                  Date.now(),
                )
                lastSentTranscriptionTime = Date.now()
                // Do something with author and content variables here
              }
            } catch (error) {
              console.dir(error)

            }
          }
        }
      }
    }
  };

  // Create a new MutationObserver instance
  const observer = new MutationObserver(callback);

  // Start observing the target node for childList mutations
  observer.observe(targetNode, { childList: true, subtree: true });
})();
