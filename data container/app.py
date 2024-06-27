from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Load the CSV data
data = pd.read_csv('container.csv')

@app.route('/forward', methods=['POST'])
def forward_data():
    request_data = request.get_json()
    if 'source' in request_data and request_data['source'] == 'allowed_source':
        return jsonify(data.to_dict(orient='records'))
    else:
        return jsonify({'message': 'Request not authorized to receive data'}), 403

@app.route('/customer_data', methods=['POST'])
def get_customer_data():
    request_data = request.get_json()
    customer_account = request_data.get('Customer Account')
    
    if customer_account:
        customer_data = data[data['Customer Account'] == customer_account]
        if not customer_data.empty:
            return jsonify(customer_data.to_dict(orient='records'))
        else:
            return jsonify({'message': 'Customer not found'}), 404
    else:
        return jsonify({'message': 'Customer Account not provided'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
