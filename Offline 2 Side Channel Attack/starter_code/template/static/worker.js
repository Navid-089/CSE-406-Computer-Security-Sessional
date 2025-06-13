/* Find the cache line size by running `getconf -a | grep CACHE` */
const LINESIZE = 64;
/* Find the L3 size by running `getconf -a | grep CACHE` */
const LLCSIZE = 16 * 1024 * 1024;
/* Collect traces for 10 seconds; you can vary this */
const TIME = 10 * 1000;
/* Collect traces every 10ms; you can vary this */
const P = 10; 

function sweep(P) {
    /*
     * Implement this function to run a sweep of the cache.
     * 1. Allocate a buffer of size LLCSIZE.
     * 2. Read each cache line (read the buffer in steps of LINESIZE).
     * 3. Count the number of times each cache line is read in a time period of P milliseconds.
     * 4. Store the count in an array of size K, where K = TIME / P.
     * 5. Return the array of counts.
     */

    const buffer = new Uint8Array(LLCSIZE);
    const K = TIME / P;
    const counts = [];

    for (let i = 0; i < K; i++) {
        const windowStart = performance.now();
        let sweepCount = 0;

        while (performance.now() - windowStart < P) {
            for (let j = 0; j < LLCSIZE; j += LINESIZE) {
                let tmp = buffer[j];
            }
            sweepCount++;
        }

        counts.push(sweepCount);
    }

    return counts;
}

self.addEventListener('message', function(e) {
    /* Call the sweep function and return the result */ 

    if(e.data === "start") {
        const result = sweep(P); 
        this.self.postMessage
    }
});