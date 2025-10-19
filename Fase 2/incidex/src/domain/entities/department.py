from src.infrastructure.persistence.database import db

class Department(db.Model):
    __tablename__ = "departments"
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False, unique=True)
