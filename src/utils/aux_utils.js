(()=>{
    
  const TIME_TO_QUIT = 120000 // quit after 2 mins
  class QuitError extends Error {
    constructor(message) {
      super(message);
      this.name = "Only 1 other user in meeting! Quitting...";
    }
  }
  function waitForElement(xpath, context, callback, timeout = 10000, intervalTime = 1000) {
    const endTime = Date.now() + timeout;

    const intervalId = setInterval(() => {
      const result = document.evaluate(
        xpath,
        context,
        null,
        XPathResult.FIRST_ORDERED_NODE_TYPE,
        null
      );

      const element = result.singleNodeValue;

      if (element) {
        clearInterval(intervalId);
        callback(element); // Pass the found element to the callback
      } else if (Date.now() > endTime) {
        clearInterval(intervalId);
        callback(new Error('Element not found within timeout period')); // Pass the error to the callback
      }
    }, intervalTime);
  }
  function waitForElementBlocking(xpath, context = document,callback, timeout = 5000) {
    const endTime = Date.now() + timeout;


    while (Date.now() < endTime){
        const result = document.evaluate(
          xpath,
          context,
          null,
          XPathResult.FIRST_ORDERED_NODE_TYPE,
          null
        );

        const element = result.singleNodeValue;

        if (element) {
          console.log("ran callback")
          callback(element)
          return;
        } 
    }
    
  }
  async function waitForElementAsync(xpath, context = document, timeout = 30000, intervalTime = 100) {
    const endTime = Date.now() + timeout;

    return new Promise((resolve, reject) => {
      const intervalId = setInterval(() => {
        const result = document.evaluate(
          xpath,
          context,
          null,
          XPathResult.FIRST_ORDERED_NODE_TYPE,
          null
        );

        const element = result.singleNodeValue;

        if (element) {
          clearInterval(intervalId);
          resolve(element);
        } else if (Date.now() > endTime) {
          clearInterval(intervalId);
          reject(new Error(xpath+' : Element not found within timeout period'));
        }
      }, intervalTime);
    });
  }
  window.waitForElement = waitForElement
  window.waitForElementAsync = waitForElementAsync
  window.waitForElementBlocking = waitForElementBlocking
  window.QuitError = QuitError
  window.TIME_TO_QUIT = TIME_TO_QUIT
})();


