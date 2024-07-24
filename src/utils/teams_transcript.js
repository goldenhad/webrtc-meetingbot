(()=>{
  // Get the div with data-tid="closed-captions-renderer"
  const targetNode = document.querySelector('div[data-tid="closed-captions-renderer"]');
  
  if (!targetNode) {
    console.error('Target node not found');
    return;
  }

  // Callback function to execute when mutations are observed
  const callback = function(mutationsList) {
    for (const mutation of mutationsList) {
      if (mutation.type === 'childList') {
        for (const addedNode of mutation.addedNodes) {
          if (addedNode.nodeType === Node.ELEMENT_NODE && addedNode.classList.contains('ui-chat__item')) {
            // Get the descendant span with class containing "ui-chat__message__author"
            const authorSpan = addedNode.querySelector('span[class*="ui-chat__message__author"]');
            const author = authorSpan ? authorSpan.textContent : null;

            // Get the span with data-tid="closed-caption-text"
            const contentSpan = addedNode.querySelector('span[data-tid="closed-caption-text"]');
            const content = contentSpan ? contentSpan.textContent : null;

            if (author && content) {
              // Save the author and content to variables or handle them as needed
              console.log('Author:', author);
              console.log('Content:', content);
              // Do something with author and content variables here
            }
          }
        }
      }
    }
  };

  // Create a new MutationObserver instance
  const observer = new MutationObserver(callback);

  // Start observing the target node for childList mutations
  observer.observe(targetNode, { childList: true, subtree: false });
})();
