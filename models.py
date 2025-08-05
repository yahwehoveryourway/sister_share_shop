from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    donations = db.relationship('Donation', foreign_keys='Donation.donor_id', backref='donor', lazy=True)
    requests = db.relationship('Request', backref='requester', lazy=True)
    approved_donations = db.relationship('Donation', foreign_keys='Donation.approved_by_id', backref='approved_by', lazy=True)
    matched_items = db.relationship('Match', foreign_keys='Match.matched_by_id', backref='matched_by', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    donations = db.relationship('Donation', backref='category', lazy=True)
    requests = db.relationship('Request', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    photo_filename = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')  # pending, approved, donated, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    donated_at = db.Column(db.DateTime)
    thank_you_sent = db.Column(db.Boolean, default=False)
    
    # Foreign keys
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    matches = db.relationship('Match', backref='donation', lazy=True)

    def __repr__(self):
        return f'<Donation {self.title}>'

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    status = db.Column(db.String(20), default='active')  # active, fulfilled, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    fulfilled_at = db.Column(db.DateTime)
    
    # Foreign keys
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    # Relationships
    matches = db.relationship('Match', backref='request', lazy=True)

    def __repr__(self):
        return f'<Request {self.title}>'

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, completed
    notes = db.Column(db.Text)
    
    # Foreign keys
    donation_id = db.Column(db.Integer, db.ForeignKey('donation.id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
    matched_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships (backref handled in User model)

    def __repr__(self):
        return f'<Match {self.id}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')  # info, success, warning, danger
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships (backref handled in User model)

    def __repr__(self):
        return f'<Notification {self.title}>'
