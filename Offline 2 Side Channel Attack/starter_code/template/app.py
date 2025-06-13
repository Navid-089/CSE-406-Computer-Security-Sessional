from flask import Flask, send_from_directory, request, jsonify, send_file
import os
import json
import numpy as np
from PIL import Image
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")  # Use a backend that doesn't require a display

# additional imports

app = Flask(__name__)

stored_traces = []
stored_heatmaps = []

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/collect_trace', methods=['POST'])
def collect_trace():
    """ 
    Implement the collect_trace endpoint to receive trace data from the frontend and generate a heatmap.
    1. Receive trace data from the frontend as JSON
    2. Generate a heatmap using matplotlib
    3. Store the heatmap and trace data in the backend temporarily
    4. Return the heatmap image and optionally other statistics to the frontend
    """

@app.route('/api/clear_results', methods=['POST'])
def clear_results():
    """ 
    Implment a clear results endpoint to reset stored data.
    1. Clear stored traces and heatmaps
    2. Return success/error message
    """
# Additional endpoints can be implemented here as needed.
@app.route("/traces", methods=["POST"])
def receive_traces():
    data = request.get_json()
    if not data or "trace" not in data:
        return jsonify({"error": "No valid trace data received"}), 400

    trace = data["trace"]

    # Save trace data
    with open("trace.json", "w") as f:
        json.dump(trace, f)
    # Convert to array for stats
    raw_array = np.array(trace)
    min_val = float(np.min(raw_array))
    max_val = float(np.max(raw_array))
    range_val = float(max_val - min_val)
    sample_count = len(trace)

    # Normalize for plotting
    norm_data = np.interp(raw_array, (min_val, max_val), (0, 255)).astype(np.uint8)

    # Remove trailing zeros (blue regions)
    nonzero_indices = np.where(norm_data > 0)[0]
    if len(nonzero_indices) == 0:
        trimmed = norm_data  # fallback: use whole
    else:
        start, end = nonzero_indices[0], nonzero_indices[-1] + 1
        trimmed = norm_data[start:end]

    # Pad if too short
    if len(trimmed) < 1000:
        padded = np.zeros((1000,), dtype=np.uint8)
        padded[:len(trimmed)] = trimmed
        trimmed = padded

    # Reshape for horizontal heatmap
    reshaped = trimmed.reshape((1, -1))  # 1 row, wide image

    # Save colorful heatmap
    filename = f"heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join("static", filename)

    plt.figure(figsize=(6, 1))
    plt.imshow(reshaped, aspect='auto', cmap='plasma')  # or 'hot', 'inferno', etc.
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(filepath, bbox_inches='tight', pad_inches=0)
    plt.close()


    stored_heatmaps.append(filename)

    return jsonify({
        "status": "received",
        "file": filename,
        "min": min_val,
        "max": max_val,
        "range": range_val,
        "samples": sample_count
    }), 200

@app.route("/heatmap", methods=["GET"])
def get_heatmap():
    path = "heatmap.png"
    if not os.path.exists(path):
        return "Heatmap not generated yet", 404
    return send_file(path, mimetype="image/png")

@app.route("/api/heatmaps", methods=["GET"])
def list_heatmaps():
    return jsonify({"heatmaps": stored_heatmaps})




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)