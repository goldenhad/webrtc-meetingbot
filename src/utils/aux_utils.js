(()=>{
function waitForElement(xpath, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const interval = 100; // Interval to check for the element
    let timeElapsed = 0;

    const intervalId = setInterval(() => {
      let element = document.evaluate(
        xpath,
        document,
        null,
        XPathResult.FIRST_ORDERED_NODE_TYPE,
        null
      ).singleNodeValue;

      if (element) {
        clearInterval(intervalId);
        resolve(element);
      }

      timeElapsed += interval;
      if (timeElapsed >= timeout) {
        clearInterval(intervalId);
        reject(new Error('Element not found within timeout period'));
      }
    }, interval);
  });
}
window.waitForElement = waitForElement;

})();
