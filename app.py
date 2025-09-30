import logging
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sys
from sqlalchemy.sql import text

app = Flask(__name__)

# Configuração do PostgreSQL via variáveis de ambiente
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_HOST = os.getenv('POSTGRES_HOST')
DB_PORT = os.getenv('POSTGRES_PORT')
DB_NAME = os.getenv('POSTGRES_DB')

# Construir a URL do banco de dados
DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

# Log das configurações do banco (sem senha por segurança)
logger.info(f"Database configuration: Host={DB_HOST}, Port={DB_PORT}, DB={DB_NAME}, User={DB_USER}")

# Inicializar o banco de dados
db = SQLAlchemy(app)

# Modelos do banco de dados
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat()
        }

class RequestLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(10), nullable=False)
    endpoint = db.Column(db.String(200), nullable=False)
    ip_address = db.Column(db.String(50))
    status_code = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'method': self.method,
            'endpoint': self.endpoint,
            'ip_address': self.ip_address,
            'status_code': self.status_code,
            'created_at': self.created_at.isoformat()
        }

# Criar tabelas (com tratamento de erro)
try:
    with app.app_context():
        db.create_all()
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

# Request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.url} from {request.remote_addr}")
    
    # Salvar no banco de dados
    try:
        log_entry = RequestLog(
            method=request.method,
            endpoint=request.url,
            ip_address=request.remote_addr
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error saving request log: {e}")
        db.session.rollback()

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
    
    # Atualizar o log com o status code
    try:
        latest_log = RequestLog.query.order_by(RequestLog.id.desc()).first()
        if latest_log:
            latest_log.status_code = response.status_code
            db.session.commit()
    except Exception as e:
        logger.error(f"Error updating request log: {e}")
        db.session.rollback()
    
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
        
        # Verificar se usuário já existe, se não, criar
        user = User.query.filter_by(name=name).first()
        if not user:
            user = User(name=name)
            db.session.add(user)
            db.session.commit()
            logger.info(f"New user created: {name}")
        
        return jsonify({
            "message": f"Hello, {name}!",
            "user": user.to_dict()
        })
    except ValueError as e:
        logger.error(f"Validation error in get_user: {e}")
        return jsonify({"error": "Name must be at least 2 characters"}), 400
    except Exception as e:
        logger.error(f"Database error in get_user: {e}")
        return jsonify({"error": "Internal server error"}), 500

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
        
        # Salvar mensagem no banco de dados
        message_entry = Message(
            message=data['message'],
            ip_address=request.remote_addr
        )
        db.session.add(message_entry)
        db.session.commit()
        
        logger.info(f"Successfully processed and saved message: {data['message']}")
        return jsonify({
            "status": "success",
            "received_message": data['message'],
            "message_id": message_entry.id,
            "response": "Data received and saved successfully!",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Unexpected error in submit_data: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Internal server error"}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    logger.info("Health check accessed")
    try:
        db.session.execute(text('SELECT 1'))
        db_status = "connected"
        
        # Estatísticas do banco
        user_count = User.query.count()
        message_count = Message.query.count()
        log_count = RequestLog.query.count()
        
    except Exception as e:
        db_status = f"error: {str(e)}"
        user_count = message_count = log_count = 0
    
    return jsonify({
        "status": "healthy",
        "database": db_status,
        "database_stats": {
            "users": user_count,
            "messages": message_count,
            "request_logs": log_count
        },
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

# Novo endpoint para listar usuários
@app.route('/users')
def list_users():
    try:
        users = User.query.all()
        return jsonify({
            "users": [user.to_dict() for user in users],
            "count": len(users)
        })
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Novo endpoint para listar mensagens
@app.route('/messages')
def list_messages():
    try:
        messages = Message.query.order_by(Message.created_at.desc()).all()
        return jsonify({
            "messages": [message.to_dict() for message in messages],
            "count": len(messages)
        })
    except Exception as e:
        logger.error(f"Error listing messages: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Run the application
if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    
    logger.info(f"Starting Flask application on {host}:{port}...")
    app.run(debug=False, host=host, port=port)