import os
import json
from flask import Flask, render_template, jsonify, request

app = Flask(__name__, template_folder='.')

@app.route('/traffic-dashboard')
def traffic_dashboard():
    return render_template('index.html')

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

@app.route('/api/update', methods=['POST'])
def update_metrics():
    incoming_data = request.json
    file_path = "live_metrics.json"
    
    data_list = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data_list = json.load(f)
        except:
            data_list = []
            
    data_list.append(incoming_data)
    
    with open(file_path, "w") as f:
        json.dump(data_list[-100:], f)
        
    return jsonify({"status": "success"}), 200

@app.route('/')
def home():
    return "Traffic Server is live! Go to /traffic-dashboard"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)