from app import db
from datetime import datetime

class ApiRequest(db.Model):
    """Track API requests for analytics"""
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    api_key_used = db.Column(db.String(20))  # Last 5 chars for privacy
    status_code = db.Column(db.Integer)
    response_time = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=False)

class ApiKeyMetrics(db.Model):
    """Track API key performance metrics"""
    id = db.Column(db.Integer, primary_key=True)
    key_suffix = db.Column(db.String(10), nullable=False)  # Last 5 chars
    total_requests = db.Column(db.Integer, default=0)
    successful_requests = db.Column(db.Integer, default=0)
    failed_requests = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    is_disabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def success_rate(self):
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
