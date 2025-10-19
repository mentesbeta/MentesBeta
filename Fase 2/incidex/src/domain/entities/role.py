from src.infrastructure.persistence.database import db

class Role(db.Model):
    __tablename__ = "roles"
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255))
