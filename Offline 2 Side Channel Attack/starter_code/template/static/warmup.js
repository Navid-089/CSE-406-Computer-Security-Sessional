/* Find the cache line size by running `getconf -a | grep CACHE` */
const LINESIZE = 64;

function readNlines(n) {
  /*
   * Implement this function to read n cache lines.
   * 1. Allocate a buffer of size n * LINESIZE.
   * 2. Read each cache line (read the buffer in steps of LINESIZE) 10 times.
   * 3. Collect total time taken in an array using `performance.now()`.
   * 4. Return the median of the time taken in milliseconds.
   */

  // printing in console for debugging
  console.log(`Reading ${n} cache lines...`);

  const LINESIZE = 64; 
  const REPEATS = 10; 
  const buffer = new Uint8Array(n * LINESIZE); 

  let times = []; 

  for (let i = 0; i < REPEATS; i++) { 
    const start = performance.now(); 

    for( let j = 0 ; j < n * LINESIZE; j += LINESIZE) { 
      let tmp = buffer[j];  
    } 

    const end = performance.now();
    times.push(end - start);
  }

  times.sort((a, b) => a - b);
  return times[Math.floor(times.length / 2)];
}

self.addEventListener("message", function (e) {
  if (e.data === "start") {
    const results = [];

    /* Call the readNlines function for n = 1, 10, ... 10,000,000 and store the result */ 

    for (let n = 1; n <= 10000000; n *= 10) {
      try {
        const latency = readNlines(n); 
        results.push({n, latency});
      } catch (error) { 
        console.error(`Error reading ${n} lines:`, error);
        results.push({n, latency: null, error: error.message});
      }
    }

    self.postMessage(results);
  }
});
