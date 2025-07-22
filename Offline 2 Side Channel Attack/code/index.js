function app() {
  return {
    /* This is the main app object containing all the application state and methods. */
    // The following properties are used to store the state of the application

    // results of cache latency measurements
    latencyResults: null,
    // local collection of trace data
    traceData: [],
    // Local collection of heapmap images
    heatmaps: [],

    // Current status message
    status: "",
    // Is any worker running?
    isCollecting: false,
    // Is the status message an error?
    statusIsError: false,
    // Show trace data in the UI?
    showingTraces: false,

    // Collect latency data using warmup.js worker
    async collectLatencyData() {
      this.isCollecting = true;
      this.status = "Collecting latency data...";
      this.latencyResults = null;
      this.statusIsError = false;
      this.showingTraces = false;

      try {
        // Create a worker
        let worker = new Worker("warmup.js");

        // Start the measurement and wait for result
        const results = await new Promise((resolve) => {
          worker.onmessage = (e) => resolve(e.data);
          worker.postMessage("start");
        });

        // Update results
        this.latencyResults = results;
        this.status = "Latency data collection complete!";

        // Terminate worker
        worker.terminate();
      } catch (error) {
        console.error("Error collecting latency data:", error);
        this.status = `Error: ${error.message}`;
        this.statusIsError = true;
      } finally {
        this.isCollecting = false;
      }
    },

    // Collect trace data using worker.js and send to backend
    async collectTraceData() {
       /* 
        * Implement this function to collect trace data.
        * 1. Create a worker to run the sweep function.
        * 2. Collect the trace data from the worker.
        * 3. Send the trace data to the backend for temporary storage and heatmap generation.
        * 4. Fetch the heatmap from the backend and add it to the local collection.
        * 5. Handle errors and update the status.
        */

       this.isCollecting = true; 
       this.status = "Collecting trace data..."; 
       this.statusIsError = false;
       this.showingTraces = false; 
       this.latencyResults = null; // Reset latency results

       try {
         const worker = new Worker("worker.js"); 

         const trace = await new Promise((resolve) => { 
          worker.onmessage = (e) => resolve(e.data);
          worker.postMessage("start");
         });

         this.traceData.push(trace); // Add trace data to local collection 

         const response = await fetch("/traces", {
           method: "POST",
           headers: {
             "Content-Type": "application/json",
           },
           body: JSON.stringify({ trace }),
         });

          if (!response.ok) {
            throw new Error("Failed to send trace data to the server");
          }

          const result = await response.json(); // parse server response
          const imageUrl = `/static/heatmaps/${result.file}`;
          
          // Store heatmap + metadata
          this.heatmaps.push({
            src: imageUrl,
            min: result.min,
            max: result.max,
            range: result.range,
            samples: result.samples
          });
          

         

          this.status = "Trace data collection complete!"; 
          this.showingTraces = true; // Show trace data in the UI

          worker.terminate(); // Terminate the worker
        }

       catch (error) {
         console.error("Error collecting trace data:", error);
         this.status = `Error: ${error.message}`;
         this.statusIsError = true;
       } finally {
        this.isCollecting = false;
       }
    },

    // Download the trace data as JSON (array of arrays format for ML)
    async downloadTraces() {
       /* 
        * Implement this function to download the trace data.
        * 1. Fetch the latest data from the backend API.
        * 2. Create a download file with the trace data in JSON format.
        * 3. Handle errors and update the status.
        * 
        */

       try {
        const response = await fetch("/api/get_results");
        if (!response.ok) throw new Error("Failed to download traces");
    
        const result = await response.json();
        const blob = new Blob([JSON.stringify(result.traces, null, 2)], {
          type: "application/json",
        });
    
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        a.download = `traces_${timestamp}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } catch (error) {
        console.error("Download failed:", error);
      }
    },

    async predictActiveWebsite() {
      this.isCollecting = true;
      this.status = "Predicting active website...";
    
      try {
        const worker = new Worker("worker.js");
    
        const trace = await new Promise((resolve) => {
          worker.onmessage = (e) => resolve(e.data);
          worker.postMessage("start");
        });
    
        worker.terminate();
    
        const response = await fetch("/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ trace }),
        });
    
        const result = await response.json();
        this.status = `Most likely website: ${result.predicted_website} (Confidence: ${(
          result.confidence * 100
        ).toFixed(1)}%)`;
        this.statusIsError = false;
      } catch (error) {
        console.error("Prediction failed:", error);
        this.status = `Error: ${error.message}`;
        this.statusIsError = true;
      } finally {
        this.isCollecting = false;
      }
    },
    

    // Clear all results from the server
    async clearResults() {
      /* 
       * Implement this function to clear all results from the server.
       * 1. Send a request to the backend API to clear all results.
       * 2. Clear local copies of trace data and heatmaps.
       * 3. Handle errors and update the status.
       */
      console.log("Clearing results...\n");
    
      try {
        const response = await fetch("/api/clear_results", {
          method: "POST",
        });
    
        if (!response.ok) throw new Error("Failed to clear results");

       
        this.traceData = [];
        this.heatmaps = [];
        this.showingTraces = false;
        this.status = "Results cleared.";
      } catch (error) {
        console.error("Clearing failed:", error);
      }
    },

    
  };
}
