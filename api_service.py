# api_service.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from serviceComposite import ServiceComposite
import re
import time

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST"], "allow_headers": ["Content-Type"]}})

# Initialize service
service = ServiceComposite()

@app.route('/')
def home():
    return "Service is running"

@app.route('/process', methods=['POST'])
def process_loan_request():
    try:
        if request.method == 'OPTIONS':
            return jsonify({}), 200
            
        content = request.json.get('content')
        if not content:
            return jsonify({
                'status': 'error',
                'message': 'Aucun contenu fourni'
            }), 400

        # Get client ID from email or generate one
        email_match = re.search(r'Email:\s*(.*?)(?=\s|$)', content)
        client_id = email_match.group(1) if email_match else f"client_{time.time()}"
        
        # Process request using service composite
        try:
            result = service.process_and_store(client_id, content)
            return jsonify({
                'status': 'success',
                'client_id': client_id,
                'client_data': result['client_data'],
                'property_evaluation': result['property_evaluation'],
                'approval_decision': result['approval_decision']
            })

        except ValueError as ve:
            # Handle property non-compliance or other validation errors
            return jsonify({
                'status': 'error',
                'message': 'Demande non valide',
                'evaluation': str(ve)
            }), 400

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/credit-check/<client_id>', methods=['GET'])
def get_credit_check(client_id):
    try:
        if request.method == 'OPTIONS':
            return jsonify({}), 200
            
        solvency = service.get_credit_check(client_id)
        client_data = service.get_client_info(client_id)
        
        return jsonify({
            'status': 'success',
            'client_id': client_id,
            'solvency': solvency,
            'client_data': client_data
        })

    except ValueError as e:
        logger.error(f"Client not found: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except Exception as e:
        logger.error(f"Error checking credit: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    try:
        port = 5000
        logger.info(f"Starting API service on port {port}...")
        app.run(host='127.0.0.1', port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")