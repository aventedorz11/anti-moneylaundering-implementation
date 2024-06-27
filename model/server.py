from flask import Flask, request, jsonify, render_template
import pickle
import pandas as pd
import requests
import numpy as np

# Load models and encoders
with open('model.pkl', 'rb') as model_file:
    model = pickle.load(model_file)

with open('encoder.pkl', 'rb') as encoder_file:
    le = pickle.load(encoder_file)

with open('scaler.pkl', 'rb') as scaler_file:
    sc = pickle.load(scaler_file)

CONTAINER_IP = 'http://127.0.0.1:5000/customer_data'

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

def fetch_container_data(customer_account):
    try:
        response = requests.post(CONTAINER_IP, json={'Customer Account': customer_account})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from container: {e}")
        return None

@app.route('/predict', methods=['POST'])
def predict():
    form_data = request.form.to_dict()
    print("Received form data:", form_data)
    
    customer_account = form_data.get('Customer Account')
    if customer_account:
        customer_data = fetch_container_data(customer_account)
        if customer_data:
            customer_df = pd.DataFrame(customer_data)
            form_df = pd.DataFrame([form_data])
            df = pd.concat([form_df, customer_df], axis=1)
            df=df.head(1)
            df = df.loc[:, ~df.columns.duplicated()]
            df['Amount of Transfer'] = pd.to_numeric(df['Amount of Transfer'], errors='coerce')
            df['Average Transaction Amount'] = pd.to_numeric(df['Average Transaction Amount'], errors='coerce')
            df['Transaction Amount Relative to Average']=df['Amount of Transfer']/df['Average Transaction Amount']
            df['Offshore Transfer']=np.where(df['Source country']==df['Receiving country'],0,1)
            desired_order=['Customer Account','Customer Bank','Amount of Transfer','Offshore Transfer','Customer Account Age','Customer Nationality','Suspicious activity found in previous transactions','KYC Complied','Receivers Account','Receivers Bank','Frequency of transaction in last 30 days','Source country','Receiving country','Transaction Type','Average Transaction Amount','Transaction Amount Relative to Average']
            df=df[desired_order]
            # Encoding
            df = le.transform(df)
            # Scaling
            scaled_data = sc.transform(df)
            
            # Predict
            prediction = model.predict(scaled_data)
            if prediction[0] == 0:
                return render_template('transaction_successful.html')
            else:
                return render_template('transaction_suspected.html')
        else:
            return jsonify({'error': 'Failed to fetch customer data'}), 500
    else:
        return jsonify({'error': 'Customer Account not provided'}), 400

@app.route('/fetch_data', methods=['GET'])
def fetch_data():
    container_data = fetch_container_data()
    
    if container_data is None:
        return jsonify({"error": "Failed to fetch data from container"}), 500

    return jsonify(container_data)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
