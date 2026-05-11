from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here_change_in_production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///challenge_master.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модели БД
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    coins = db.Column(db.Integer, default=0)
    crystals = db.Column(db.Integer, default=0)
    power_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(10), default='uk')  # uk, ru, pl, en
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    fighters = db.relationship('Fighter', backref='owner', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('ChatMessage', backref='author', lazy=True, cascade='all, delete-orphan')
    game_stats = db.relationship('GameStats', backref='player', lazy=True, cascade='all, delete-orphan')

class Fighter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    fighter_type = db.Column(db.String(50), nullable=False)  # brawl_stars, cs2, gta5
    level = db.Column(db.Integer, default=1)
    health = db.Column(db.Integer, default=100)
    attack = db.Column(db.Integer, default=10)
    defense = db.Column(db.Integer, default=5)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PromoCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    reward_coins = db.Column(db.Integer, default=0)
    reward_crystals = db.Column(db.Integer, default=0)
    reward_power_points = db.Column(db.Integer, default=0)
    max_uses = db.Column(db.Integer, default=-1)  # -1 = unlimited
    uses_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room = db.Column(db.String(50), nullable=False)  # challenges, games, shop, etc
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GameStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_name = db.Column(db.String(100), nullable=False)
    high_score = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)

class DailyTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    reward_coins = db.Column(db.Integer, default=0)
    reward_crystals = db.Column(db.Integer, default=0)
    reward_power_points = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

# Языки
LANGUAGES = {
    'uk': {
        'title': 'Challenge Master: Global Stumble Battle',
        'home': 'Головна',
        'challenges': 'Челленджи',
        'games': 'Ігри',
        'shop': 'Магазин',
        'leaderboard': 'Таблиця лідерів',
        'profile': 'Профіль',
        'logout': 'Вихід',
        'login': 'Вхід',
        'register': 'Реєстрація',
        'email': 'Email',
        'password': 'Пароль',
        'username': 'Ім\'я користувача',
        'coins': 'Монети',
        'crystals': 'Кристали',
        'power_points': 'Очки сили',
        'level': 'Рівень',
        'fighters': 'Бійці',
        'upgrade': 'Прокачати',
        'buy': 'Купити',
        'sell': 'Продати',
        'settings': 'Налаштування',
        'admin_panel': 'Адмін-панель',
    },
    'ru': {
        'title': 'Challenge Master: Global Stumble Battle',
        'home': 'Главная',
        'challenges': 'Челленджи',
        'games': 'Игры',
        'shop': 'Магазин',
        'leaderboard': 'Таблица лидеров',
        'profile': 'Профиль',
        'logout': 'Выход',
        'login': 'Вход',
        'register': 'Регистрация',
        'email': 'Email',
        'password': 'Пароль',
        'username': 'Имя пользователя',
        'coins': 'Монеты',
        'crystals': 'Кристаллы',
        'power_points': 'Очки силы',
        'level': 'Уровень',
        'fighters': 'Боец',
        'upgrade': 'Улучшить',
        'buy': 'Купить',
        'sell': 'Продать',
        'settings': 'Настройки',
        'admin_panel': 'Админ-панель',
    },
    'pl': {
        'title': 'Challenge Master: Global Stumble Battle',
        'home': 'Strona główna',
        'challenges': 'Wyzwania',
        'games': 'Gry',
        'shop': 'Sklep',
        'leaderboard': 'Tablica wyników',
        'profile': 'Profil',
        'logout': 'Wyloguj',
        'login': 'Logowanie',
        'register': 'Rejestracja',
        'email': 'Email',
        'password': 'Hasło',
        'username': 'Nazwa użytkownika',
        'coins': 'Monety',
        'crystals': 'Kryształy',
        'power_points': 'Punkty siły',
        'level': 'Poziom',
        'fighters': 'Walczący',
        'upgrade': 'Ulepsz',
        'buy': 'Kup',
        'sell': 'Sprzedaj',
        'settings': 'Ustawienia',
        'admin_panel': 'Panel Admina',
    },
    'en': {
        'title': 'Challenge Master: Global Stumble Battle',
        'home': 'Home',
        'challenges': 'Challenges',
        'games': 'Games',
        'shop': 'Shop',
        'leaderboard': 'Leaderboard',
        'profile': 'Profile',
        'logout': 'Logout',
        'login': 'Login',
        'register': 'Register',
        'email': 'Email',
        'password': 'Password',
        'username': 'Username',
        'coins': 'Coins',
        'crystals': 'Crystals',
        'power_points': 'Power Points',
        'level': 'Level',
        'fighters': 'Fighters',
        'upgrade': 'Upgrade',
        'buy': 'Buy',
        'sell': 'Sell',
        'settings': 'Settings',
        'admin_panel': 'Admin Panel',
    }
}

def get_lang():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return user.language
    return request.args.get('lang', 'uk')

def is_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.is_admin:
            return {'error': 'Access denied'}, 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html', lang=get_lang(), languages=LANGUAGES)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if user and check_password_hash(user.password, data['password']):
            session['user_id'] = user.id
            return {'success': True, 'user_id': user.id}
        return {'success': False, 'error': 'Invalid credentials'}, 401
    
    return render_template('login.html', lang=get_lang(), languages=LANGUAGES)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        
        if User.query.filter_by(email=data['email']).first():
            return {'success': False, 'error': 'Email already exists'}, 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            password=generate_password_hash(data['password'])
        )
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        return {'success': True, 'user_id': user.id}
    
    return render_template('register.html', lang=get_lang(), languages=LANGUAGES)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/user')
def get_user():
    if 'user_id' not in session:
        return {'error': 'Not authenticated'}, 401
    
    user = User.query.get(session['user_id'])
    return {
        'id': user.id,
        'username': user.username,
        'coins': user.coins,
        'crystals': user.crystals,
        'power_points': user.power_points,
        'level': user.level,
        'experience': user.experience,
        'language': user.language,
        'is_admin': user.is_admin
    }

@app.route('/api/user/language/<lang>', methods=['POST'])
def set_language(lang):
    if 'user_id' not in session:
        return {'error': 'Not authenticated'}, 401
    
    if lang not in LANGUAGES:
        return {'error': 'Invalid language'}, 400
    
    user = User.query.get(session['user_id'])
    user.language = lang
    db.session.commit()
    
    return {'success': True}

@app.route('/challenges')
def challenges():
    return render_template('challenges.html', lang=get_lang(), languages=LANGUAGES)

@app.route('/games')
def games():
    return render_template('games.html', lang=get_lang(), languages=LANGUAGES)

@app.route('/games/<game_name>')
def play_game(game_name):
    return render_template(f'games/{game_name}.html', lang=get_lang(), languages=LANGUAGES)

@app.route('/shop')
def shop():
    return render_template('shop.html', lang=get_lang(), languages=LANGUAGES)

@app.route('/leaderboard')
def leaderboard():
    users = User.query.order_by(User.experience.desc()).limit(100).all()
    return render_template('leaderboard.html', users=users, lang=get_lang(), languages=LANGUAGES)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user, lang=get_lang(), languages=LANGUAGES)

@app.route('/api/promo/use', methods=['POST'])
def use_promo():
    if 'user_id' not in session:
        return {'error': 'Not authenticated'}, 401
    
    data = request.get_json()
    promo = PromoCode.query.filter_by(code=data['code'], is_active=True).first()
    
    if not promo:
        return {'error': 'Invalid promo code'}, 400
    
    if promo.max_uses != -1 and promo.uses_count >= promo.max_uses:
        return {'error': 'Promo code limit reached'}, 400
    
    user = User.query.get(session['user_id'])
    user.coins += promo.reward_coins
    user.crystals += promo.reward_crystals
    user.power_points += promo.reward_power_points
    promo.uses_count += 1
    
    db.session.commit()
    
    return {'success': True, 'rewards': {
        'coins': promo.reward_coins,
        'crystals': promo.reward_crystals,
        'power_points': promo.reward_power_points
    }}

@app.route('/api/chat/<room>', methods=['GET', 'POST'])
def chat(room):
    if request.method == 'POST':
        if 'user_id' not in session:
            return {'error': 'Not authenticated'}, 401
        
        data = request.get_json()
        message = ChatMessage(
            user_id=session['user_id'],
            room=room,
            message=data['message']
        )
        db.session.add(message)
        db.session.commit()
        
        user = User.query.get(session['user_id'])
        return {
            'id': message.id,
            'username': user.username,
            'message': message.message,
            'created_at': message.created_at.isoformat()
        }
    
    messages = ChatMessage.query.filter_by(room=room).order_by(ChatMessage.created_at.desc()).limit(50).all()
    return [{
        'id': m.id,
        'username': m.author.username,
        'message': m.message,
        'created_at': m.created_at.isoformat()
    } for m in reversed(messages)]

@app.route('/admin')
@is_admin
def admin_panel():
    return render_template('admin.html', lang=get_lang(), languages=LANGUAGES)

@app.route('/api/admin/promos', methods=['GET', 'POST'])
@is_admin
def manage_promos():
    if request.method == 'POST':
        data = request.get_json()
        promo = PromoCode(
            code=data['code'],
            reward_coins=data.get('reward_coins', 0),
            reward_crystals=data.get('reward_crystals', 0),
            reward_power_points=data.get('reward_power_points', 0),
            max_uses=data.get('max_uses', -1)
        )
        db.session.add(promo)
        db.session.commit()
        return {'success': True, 'id': promo.id}
    
    promos = PromoCode.query.all()
    return [{
        'id': p.id,
        'code': p.code,
        'reward_coins': p.reward_coins,
        'reward_crystals': p.reward_crystals,
        'reward_power_points': p.reward_power_points,
        'max_uses': p.max_uses,
        'uses_count': p.uses_count,
        'is_active': p.is_active
    } for p in promos]

@app.route('/api/admin/users', methods=['GET'])
@is_admin
def manage_users():
    users = User.query.all()
    return [{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'coins': u.coins,
        'crystals': u.crystals,
        'power_points': u.power_points,
        'level': u.level,
        'is_admin': u.is_admin
    } for u in users]

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
