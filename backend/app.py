from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import datetime

app = Flask(__name__)
CORS(app) # Разрешаем запросы с React

# Конфигурация
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///road_monitoring.db'
app.config['JWT_SECRET_KEY'] = 'super-secret-key-123'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
jwt = JWTManager(app)

# --- МОДЕЛИ ДАННЫХ (SQL) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Road(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50))
    temp = db.Column(db.Integer)
    visibility = db.Column(db.String(20))

# Создание таблиц и начальных данных
with app.app_context():
    db.create_all()
    if not Road.query.first():
        db.session.add(Road(name="Трасса М-4", status="Норма", temp=-5, visibility="1500м"))
        db.session.commit()

# --- ЭНДПОИНТЫ API ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    # Упрощенная проверка для диплома
    if data.get('username') == 'admin' and data.get('password') == 'admin':
        token = create_access_token(identity='admin')
        return jsonify(token=token), 200
    return jsonify({"msg": "Ошибка входа"}), 401

@app.route('/api/roads', methods=['GET'])
def get_roads():
    roads = Road.query.all()
    return jsonify([{"id": r.id, "name": r.name, "status": r.status, "temp": r.temp, "visibility": r.visibility} for r in roads])

@app.route('/api/roads', methods=['POST'])
@jwt_required()
def add_road():
    data = request.json
    new_road = Road(name=data['name'], status=data['status'], temp=data['temp'], visibility=data['visibility'])
    db.session.add(new_road)
    db.session.commit()
    return jsonify({"msg": "Данные обновлены"}), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)