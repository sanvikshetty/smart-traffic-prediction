from pathlib import Path
import sys
from datetime import timedelta
import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from app.database.connection import engine, SessionLocal
from app.database.connection import DATABASE_URL
from sqlalchemy import text
from ml.models.gcn_model import TrafficGCN

MODEL=ROOT/'ml'/'models'/'gcn.pt'

LEVELS=lambda v: 'SEVERE' if v>=120 else 'HIGH' if v>=90 else 'MEDIUM' if v>=65 else 'LOW'

def main():
    if not MODEL.exists():
        raise RuntimeError('Train the GCN first: python ml/training/train_gcn.py')
    ckpt=torch.load(MODEL,map_location='cpu',weights_only=False)
    sensors=ckpt['sensors']; mean=ckpt['mean']; std=ckpt['std']
    edges=torch.tensor(ckpt['edges'],dtype=torch.long).t().contiguous()
    model=TrafficGCN(4,32); model.load_state_dict(ckpt['state_dict']); model.eval()
    q='''SELECT recorded_at,sensor_id,vehicle_count,average_speed FROM traffic_readings
          WHERE sensor_id IN :sensors ORDER BY recorded_at DESC'''
    # SQLAlchemy expanding tuple is awkward here, so fetch the five known sensor IDs.
    df=pd.read_sql("SELECT recorded_at,sensor_id,vehicle_count,average_speed FROM traffic_readings ORDER BY recorded_at DESC",engine)
    pivot=df.pivot_table(index='recorded_at',columns='sensor_id',values='vehicle_count').sort_index()[sensors].dropna()
    if len(pivot)<4: raise RuntimeError('Need at least four complete time steps.')
    history=pivot.values[-4:].astype(np.float32)
    latest_time=pivot.index[-1]
    session=SessionLocal()
    try:
        for horizon in (15,30,60):
            steps=horizon//15
            current=history.copy()
            with torch.no_grad():
                pred=None
                for _ in range(steps):
                    x=torch.tensor((current.T-mean)/std,dtype=torch.float32)
                    pred=model(x,edges).numpy()*std+mean
                    current=np.vstack([current[1:],pred])
            target=latest_time.to_pydatetime()+timedelta(minutes=horizon)
            for sid,val in zip(sensors,pred):
                session.execute(text('''INSERT INTO predictions(sensor_id,target_time,horizon_minutes,predicted_volume,predicted_speed,predicted_congestion,model_name)
                    SELECT :sid,:target,:h,:volume,LEAST(80,GREATEST(10,AVG(average_speed))),:level,'GCN'
                    FROM traffic_readings WHERE sensor_id=:sid'''),
                    {'sid':sid,'target':target,'h':horizon,'volume':float(max(0,val)),'level':LEVELS(float(val))})
        session.commit()
        print('Stored 15, 30 and 60 minute GCN predictions.')
    finally: session.close()

if __name__=='__main__': main()
