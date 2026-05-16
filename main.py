import os
import json
from flask import Flask, render_template, jsonify, request

app = Flask(__name__, template_folder='.')

# 1. Dashboard UI
@app.route('/traffic-dashboard')
def traffic_dashboard():
    return render_template('index.html')

# 2. GET Endpoint: Frontend reads data from here
@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    file_path = "live_metrics.json"
    if not os.path.exists(file_path):
        return jsonify([])
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return jsonify(data[-40:])
    except Exception as e:
        return jsonify([])

# 3. 🚀 NEW POST Endpoint: Your laptop sends data here
@app.route('/api/update', methods=['POST'])
def update_metrics():
    incoming_data = request.json
    file_path = "live_metrics.json"
    
    # Read existing data or start fresh
    data_list = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data_list = json.load(f)
        except:
            data_list = []
            
    # Append the new metrics received from your laptop
    data_list.append(incoming_data)
    
    # Save it back to the server file
    with open(file_path, "w") as f:
        json.dump(data_list[-100:], f) # Keep last 100 entries to save space
        
    return jsonify({"status": "success", "message": "Data received"}), 200

@app.route('/')
def home():
    return "Traffic AI Server is running! Go to <a href='/traffic-dashboard'>/traffic-dashboard</a>."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)