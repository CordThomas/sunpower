from app import db
from datetime import datetime
from marshmallow import Schema, fields

class Energy(db.Model):

  __tablename__ = 'sunpower'
  
  tdate = db.Column(db.Date, index=True, default=datetime.utcnow, primary_key=True)
  ttime = db.Column(db.Time, index=False, primary_key=True)
  ep = db.Column(db.Numeric(precision=5, scale=3))
  eu = db.Column(db.Numeric(precision=5, scale=3))
  mp = db.Column(db.Numeric(precision=5, scale=3))

  def __repr__(self):
    return '<Energy {}>'.format(self.ep)

class EnergySchema(Schema):
  tdate = fields.Date()
  ttime = fields.Date()
  ep = fields.Number()
  eu = fields.Number()
  mp = fields.Number()

