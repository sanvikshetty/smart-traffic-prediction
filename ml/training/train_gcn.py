from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.linear_model import LinearRegression
from torch_geometric.data import Data

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from app.database.connection import engine
from ml.models.gcn_model import TrafficGCN

MODEL_DIR=ROOT/'ml'/'models'
MODEL_DIR.mkdir(exist_ok=True)

# Static road graph. IDs match the relational seed data.
SENSORS=['S001','S002','S003','S004','S005']
EDGES=[(0,1),(1,0),(1,2),(2,1),(1,3),(3,1),(2,4),(4,2),(3,4),(4,3),(4,0),(0,4)]
EDGE_INDEX=torch.tensor(EDGES,dtype=torch.long).t().contiguous()

def load_data():
    q='''SELECT sensor_id, recorded_at, vehicle_count FROM traffic_readings ORDER BY recorded_at, sensor_id'''
    df=pd.read_sql(q,engine)
    pivot=df.pivot_table(index='recorded_at',columns='sensor_id',values='vehicle_count').sort_index()
    pivot=pivot[SENSORS].dropna()
    return pivot

def make_samples(pivot, window=4):
    X=[]; y=[]
    values=pivot.values.astype(np.float32)
    for i in range(window,len(values)):
        # node x feature matrix: each node receives its last 4 traffic volumes
        X.append(values[i-window:i].T)
        y.append(values[i])
    return np.array(X),np.array(y)

def main():
    pivot=load_data()
    X,y=make_samples(pivot)
    if len(X)<10:
        raise RuntimeError('Not enough traffic history to train. Load more data first.')
    split=max(1,int(len(X)*0.8))
    x_train,x_test=X[:split],X[split:]
    y_train,y_test=y[:split],y[split:]

    # Normalize using training distribution only.
    mean=float(x_train.mean()); std=float(x_train.std()+1e-6)
    model=TrafficGCN(in_channels=4,hidden=32)
    opt=torch.optim.Adam(model.parameters(),lr=0.01,weight_decay=1e-4)
    loss_fn=torch.nn.MSELoss()
    model.train()
    for epoch in range(1,151):
        total=0.0
        for features,target in zip(x_train,y_train):
            x=torch.tensor((features-mean)/std,dtype=torch.float32)
            target_t=torch.tensor((target-mean)/std,dtype=torch.float32)
            pred=model(x,EDGE_INDEX)
            loss=loss_fn(pred,target_t)
            opt.zero_grad(); loss.backward(); opt.step(); total+=float(loss)
        if epoch % 30 == 0:
            print(f'epoch={epoch} loss={total/len(x_train):.4f}')

    model.eval(); preds=[]
    with torch.no_grad():
        for features in x_test:
            x=torch.tensor((features-mean)/std,dtype=torch.float32)
            p=model(x,EDGE_INDEX).numpy()*std+mean
            preds.append(p)
    pred=np.array(preds)
    mae=mean_absolute_error(y_test.flatten(),pred.flatten())
    rmse=float(np.sqrt(mean_squared_error(y_test.flatten(),pred.flatten())))
    nonzero=np.where(y_test.flatten()==0,1,y_test.flatten())
    mape=float(np.mean(np.abs((y_test.flatten()-pred.flatten())/nonzero))*100)

    # Comparable simple baseline: linear regression on the flattened 4-lag features per node.
    lr=LinearRegression().fit(x_train.reshape(len(x_train),-1),y_train)
    base=lr.predict(x_test.reshape(len(x_test),-1))
    bmae=mean_absolute_error(y_test.flatten(),base.flatten())
    brmse=float(np.sqrt(mean_squared_error(y_test.flatten(),base.flatten())))
    bmape=float(np.mean(np.abs((y_test.flatten()-base.flatten())/nonzero))*100)

    torch.save({'state_dict':model.state_dict(),'mean':mean,'std':std,'sensors':SENSORS,'edges':EDGES},MODEL_DIR/'gcn.pt')
    metrics={'gcn':{'MAE':float(mae),'RMSE':rmse,'MAPE':mape},'linear_regression':{'MAE':float(bmae),'RMSE':brmse,'MAPE':bmape},'samples':int(len(X))}
    (MODEL_DIR/'metrics.json').write_text(json.dumps(metrics,indent=2))
    print(json.dumps(metrics,indent=2))

if __name__=='__main__': main()
