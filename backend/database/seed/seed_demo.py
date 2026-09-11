from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
import os
os.chdir(ROOT/'backend')
sys.path.insert(0,str(ROOT/'backend'))
from datetime import datetime, timedelta, timezone
from app.core.database import SessionLocal, create_tables
from hashlib import pbkdf2_hmac
from secrets import token_hex
def hash_password(password: str) -> str:
    salt=token_hex(16); digest=pbkdf2_hmac("sha256",password.encode(),salt.encode(),210_000).hex(); return f"pbkdf2_sha256$210000${salt}${digest}"
from app.models.models import User,Farm,Resource,ResourceRequest,Booking,LabourProvider,MarketOrder,Notification

DB=ROOT/'backend'/'farmgrid.db'
create_tables(); db=SessionLocal()
try:
    def user(email,name,role):
        x=db.query(User).filter_by(email=email).first()
        if not x:
            x=User(name=name,email=email,password_hash=hash_password('farmgrid123'),role=role); db.add(x); db.flush()
        return x
    farmer=user('farmer@farmgrid.demo','Demo Farmer','farmer')
    owner=user('owner@farmgrid.demo','Resource Owner','resource_owner')
    admin=user('admin@farmgrid.demo','FarmGrid Admin','admin')
    buyer=user('buyer@farmgrid.demo','Demo Buyer','buyer')
    if not db.query(Farm).filter_by(farmer_id=farmer.id).first():
        db.add(Farm(farmer_id=farmer.id,name='Green Valley Farm',location='Bengaluru',land_size_acres=5,soil_type='Loamy',soil_color='Brown',moisture=55,water_availability=70,previous_crop='Maize',previous_yield=2500))
    if not db.query(Resource).filter_by(name='Tractor A').first():
        base=datetime.now(timezone.utc).replace(hour=6,minute=0,second=0,microsecond=0)
        db.add(Resource(owner_id=owner.id,name='Tractor A',resource_type='tractor',specifications='45 HP',location='Bengaluru',latitude=12.9716,longitude=77.5946,operating_from=base,operating_until=base+timedelta(hours=14),status='available',maintenance_status='operational'))
        db.add(Resource(owner_id=owner.id,name='Harvester B',resource_type='harvester',specifications='Multi-crop harvester',location='Bengaluru',latitude=12.98,longitude=77.61,operating_from=base,operating_until=base+timedelta(hours=14),status='available',maintenance_status='operational'))
    db.flush()
    farm=db.query(Farm).filter_by(farmer_id=farmer.id).first(); tractor=db.query(Resource).filter_by(name='Tractor A').first()
    if not db.query(ResourceRequest).filter_by(farmer_id=farmer.id).first():
        start=datetime.now(timezone.utc)+timedelta(hours=6); end=start+timedelta(hours=12)
        db.add(ResourceRequest(farmer_id=farmer.id,farm_id=farm.id,resource_type='tractor',requested_resource_id=tractor.id,earliest_start=start,latest_end=end,duration_minutes=120,crop='Tomato',crop_stage='flowering',urgency_score=20,weather_risk_score=15,crop_readiness_score=16,logistics_score=8,resource_constraints_score=4,status='pending'))
    if not db.query(LabourProvider).filter_by(name='Ravi Labour Contractor').first():
        db.add(LabourProvider(user_id=owner.id,provider_type='contractor',name='Ravi Labour Contractor',region='Bengaluru',workers_available=20,skills='Harvesting, planting, spraying',daily_wage_per_worker=650,is_active=True))
        db.add(LabourProvider(user_id=None,provider_type='direct',name='Local Worker Group',region='Bengaluru',workers_available=8,skills='Weeding, harvesting',daily_wage_per_worker=550,is_active=True))
    if not db.query(MarketOrder).filter_by(buyer_id=buyer.id).first():
        db.add(MarketOrder(buyer_id=buyer.id,crop='Tomato',quantity_kg=500,quality_grade='A',required_date=datetime.now(timezone.utc)+timedelta(days=7),location='Bengaluru',offered_price_per_kg=32,status='open'))
    if not db.query(Notification).filter_by(user_id=farmer.id,title='Welcome to FarmGrid').first():
        db.add(Notification(user_id=farmer.id,title='Welcome to FarmGrid',message='Your demo farm is ready. Try creating a resource request and allocating a tractor.',notification_type='welcome'))
    db.commit(); print(f'Database ready: {DB}')
finally: db.close()
