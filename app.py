import logging
from flask import Flask, request, jsonify
from datetime import datetime
import sys

# Create Flask application instance - CORREÇÃO AQUI
app = Flask(__name__)  # __name__ com underscores duplos, não 'name'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create logger
logger = logging.getLogger(__name__)

# Request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.url} from {request.remote_addr}")
    if request.method == 'POST':
        logger.info(f"Request data: {request.get_data()}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
    return response

# Error handler
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 Error: {request.method} {request.url} - {error}")
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Error: {request.method} {request.url} - {error}")
    return jsonify({"error": "Internal server error"}), 500

# Define a simple route
@app.route('/')
def hello():
    logger.info("Hello endpoint accessed")
    return "Hello, World!"

# GET request - retrieve user info
@app.route('/user/<name>')
def get_user(name):
    logger.info(f"User endpoint accessed for: {name}")
    try:
        if len(name) < 2:
            raise ValueError("Name too short")
        return f"Hello, {name}! This is a GET request."
    except ValueError as e:
        logger.error(f"Validation error in get_user: {e}")
        return jsonify({"error": "Name must be at least 2 characters"}), 400

# POST request - create/submit data
@app.route('/submit', methods=['POST'])
def submit_data():
    logger.info("Submit endpoint accessed")
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data received in submit")
            return jsonify({"status": "error", "message": "No JSON data received"}), 400
        
        if 'message' not in data:
            logger.warning("Missing 'message' field in submit data")
            return jsonify({"status": "error", "message": "Missing 'message' field"}), 400
        
        logger.info(f"Successfully processed message: {data['message']}")
        return jsonify({
            "status": "success",
            "received_message": data['message'],
            "response": "Data received successfully!",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Unexpected error in submit_data: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    logger.info("Health check accessed")
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

# Run the application
if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(debug=True, host='0.0.0.0', port=5000)