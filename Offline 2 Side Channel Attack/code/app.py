from flask import Flask, send_from_directory, request, jsonify, send_file
import os
import json
import numpy as np
from PIL import Image
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib

import torch 
from train import ComplexFingerprintClassifier, INPUT_SIZE, HIDDEN_SIZE 
import torch.nn.functional as F
WEBSITES = [
    "https://cse.buet.ac.bd/moodle/",
    "https://google.com",
    "https://prothomalo.com",
]

MODEL_PATH = "saved_models/complex_cnn.pt"
model = ComplexFingerprintClassifier(INPUT_SIZE, HIDDEN_SIZE, len(WEBSITES))
model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device("cpu")))
model.eval()

HEATMAP_DIR = os.path.join("static", "heatmaps")
os.makedirs(HEATMAP_DIR, exist_ok=True)

matplotlib.use("Agg") 

app = Flask(__name__)

stored_traces = []
stored_heatmaps = []

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route("/traces", methods=["POST"])
def receive_traces():
    data = request.get_json()
    if not data or "trace" not in data:
        return jsonify({"error": "No valid trace data received"}), 400

    trace = data["trace"]
    stored_traces.append(trace)  

    # Save to file
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
        trimmed = norm_data
    else:
        start, end = nonzero_indices[0], nonzero_indices[-1] + 1
        trimmed = norm_data[start:end]

    # Pad if too short
    if len(trimmed) < 1000:
        padded = np.zeros((1000,), dtype=np.uint8)
        padded[:len(trimmed)] = trimmed
        trimmed = padded

    reshaped = trimmed.reshape((1, -1))

    # Save colorful heatmap
    filename = f"heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(HEATMAP_DIR, filename)

    plt.figure(figsize=(6, 1))
    plt.imshow(reshaped, aspect='auto', cmap='plasma')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(filepath, bbox_inches='tight', pad_inches=0)
    plt.close()

    stored_heatmaps.append(f"heatmaps/{filename}")


    return jsonify({
        "status": "received",
        "file": filename,
        "min": min_val,
        "max": max_val,
        "range": range_val,
        "samples": sample_count
    }), 200

@app.route("/api/get_results", methods=["GET"])
def get_results():
    return jsonify({"traces": stored_traces})

@app.route("/api/clear_results", methods=["POST"])
def clear_results():
    stored_traces.clear()
    stored_heatmaps.clear()
    return jsonify({"status": "Cleared"}), 200

@app.route("/api/heatmaps", methods=["GET"])
def list_heatmaps():
    return jsonify({"heatmaps": stored_heatmaps})

@app.route("/heatmap", methods=["GET"])
def get_heatmap():
    path = "heatmap.png"
    if not os.path.exists(path):
        return "Heatmap not generated yet", 404
    return send_file(path, mimetype="image/png")

@app.route("/predict", methods=["POST"])
def predict_trace():
    data = request.get_json()
    trace = data.get("trace", [])

    # Ensure it's a flat float32 NumPy array
    arr = np.array(trace, dtype=np.float32).flatten()
    assert isinstance(arr, np.ndarray), f"arr is not ndarray, got {type(arr)}"



    # Pad or trim to match input size
    if len(arr) < INPUT_SIZE:
        padded = np.zeros((INPUT_SIZE,), dtype=np.float32)
        padded[:len(arr)] = arr
        arr = padded
    else:
        arr = arr[:INPUT_SIZE]
    
    tensor = torch.from_numpy(arr).unsqueeze(0)



    with torch.no_grad():
        logits = model(tensor)
        probs = F.softmax(logits, dim=1)
        pred = torch.argmax(probs, dim=1).item()
        confidence = probs[0][pred].item()

    return jsonify({
        "predicted_website": WEBSITES[pred],
        "confidence": round(confidence, 4)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
