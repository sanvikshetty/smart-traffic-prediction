"""Small, dependency-light GCN prediction service for the pre-final demo.

It reads the user's four-table PostgreSQL graph (traffic_nodes, road_edges,
traffic_data, traffic_predictions), trains a two-layer graph convolution on
the latest state, and writes a 15-minute prediction back to PostgreSQL.
With only one timestamp per node, the target is a documented development
proxy; adding historical timestamps enables true supervised forecasting.
"""
from datetime import datetime, timezone
import math
import numpy as np
import torch
import torch.nn as nn
from sqlalchemy import text


class GCN(nn.Module):
    def __init__(self, in_features=3, hidden=32, out_features=3):
        super().__init__()
        self.w1 = nn.Linear(in_features, hidden)
        self.w2 = nn.Linear(hidden, hidden)
        self.out = nn.Linear(hidden, out_features)

    def forward(self, x, a):
        h = torch.relu(self.w1(a @ x))
        h = torch.relu(self.w2(a @ h))
        return self.out(a @ h)


def _adjacency(n, edges):
    a = np.eye(n, dtype=np.float32)
    for e in edges:
        vals = list(e.values())
        # road_edges created by the project stores source/target IDs; fall back
        # to the first two integer-like values if names differ.
        src = next((e[k] for k in e if k.lower() in {
            'source_node_id','from_node_id','start_node_id','source_id','from_node'
        }), None)
        dst = next((e[k] for k in e if k.lower() in {
            'target_node_id','to_node_id','end_node_id','target_id','to_node'
        }), None)
        if src is None or dst is None:
            ints = [v for v in vals if isinstance(v, (int, np.integer))]
            if len(ints) >= 2:
                src, dst = ints[0], ints[1]
        if src is None or dst is None:
            continue
        i, j = int(src)-1, int(dst)-1
        if 0 <= i < n and 0 <= j < n:
            a[i, j] = a[j, i] = 1.0
    d = a.sum(1)
    inv = np.diag(1.0 / np.sqrt(np.maximum(d, 1e-8)))
    return torch.tensor(inv @ a @ inv, dtype=torch.float32)


def _table_exists(db, name):
    return bool(db.execute(text("""
        SELECT EXISTS(SELECT 1 FROM information_schema.tables
        WHERE table_schema='public' AND table_name=:name)
    """), {'name': name}).scalar())


def run_gnn_prediction(db, epochs=300):
    required = ['traffic_nodes', 'road_edges', 'traffic_data']
    missing = [t for t in required if not _table_exists(db, t)]
    if missing:
        raise RuntimeError('Missing project tables: ' + ', '.join(missing))

    nodes = [dict(r) for r in db.execute(text(
        'SELECT node_id,node_name,latitude,longitude,road_type FROM traffic_nodes ORDER BY node_id'
    )).mappings().all()]
    edges = [dict(r) for r in db.execute(text('SELECT * FROM road_edges')).mappings().all()]
    traffic = [dict(r) for r in db.execute(text("""
        SELECT node_id,vehicle_count,average_speed,congestion_level,recorded_at
        FROM traffic_data ORDER BY recorded_at DESC
    """)).mappings().all()]

    n = len(nodes)
    latest = {}
    for r in traffic:
        latest.setdefault(int(r['node_id']), r)
    x_np = np.zeros((n, 3), dtype=np.float32)
    for i, node in enumerate(nodes):
        r = latest.get(int(node['node_id']))
        if r:
            x_np[i] = [float(r['vehicle_count'] or 0), float(r['average_speed'] or 0), float(r['congestion_level'] or 0)]

    if n == 0:
        raise RuntimeError('traffic_nodes is empty')

    # Development target: a short-horizon state proxy. Replace with actual
    # future observations once multiple timestamps are collected.
    y_np = x_np.copy()
    y_np[:, 0] *= 1.0 + 0.08 * x_np[:, 2]
    y_np[:, 1] *= np.maximum(0.65, 1.0 - 0.10 * x_np[:, 2])
    y_np[:, 2] = np.clip(x_np[:, 2] * 1.05, 0, 1)

    mean = x_np.mean(0); std = x_np.std(0); std[std < 1e-6] = 1.0
    x = torch.tensor((x_np-mean)/std, dtype=torch.float32)
    y = torch.tensor((y_np-mean)/std, dtype=torch.float32)
    a = _adjacency(n, edges)

    torch.manual_seed(42)
    model = GCN()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=1e-4)
    loss_fn = nn.MSELoss()
    model.train()
    for _ in range(max(50, min(int(epochs), 1000))):
        optimizer.zero_grad()
        loss = loss_fn(model(x, a), y)
        loss.backward(); optimizer.step()

    model.eval()
    with torch.no_grad():
        pred = model(x, a).numpy() * std + mean
    pred[:, 0] = np.maximum(pred[:, 0], 0)
    pred[:, 1] = np.maximum(pred[:, 1], 0)
    pred[:, 2] = np.clip(pred[:, 2], 0, 1)

    now = datetime.now(timezone.utc)
    rows = []
    for i, node in enumerate(nodes):
        rows.append({
            'node_id': int(node['node_id']),
            'node_name': node['node_name'],
            'prediction_time': now,
            'predicted_vehicle_count': round(float(pred[i,0]), 2),
            'predicted_speed': round(float(pred[i,1]), 2),
            'predicted_congestion_level': round(float(pred[i,2]), 3),
        })

    if _table_exists(db, 'traffic_predictions'):
        columns = {r[0] for r in db.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema='public' AND table_name='traffic_predictions'
        """)).all()}
        for r in rows:
            # Write only columns present in the user's existing table.
            data = {
                'node_id': r['node_id'], 'prediction_time': r['prediction_time'],
                'predicted_vehicle_count': r['predicted_vehicle_count'],
                'predicted_speed': r['predicted_speed'],
                'predicted_congestion_level': r['predicted_congestion_level'],
                'predicted_congestion': r['predicted_congestion_level'],
            }
            usable = [k for k in data if k in columns]
            if usable:
                db.execute(text(
                    f"INSERT INTO traffic_predictions ({','.join(usable)}) VALUES ({','.join(':'+k for k in usable)})"
                ), {k:data[k] for k in usable})
        db.commit()

    return {'generated_at': now.isoformat(), 'model':'GCN-2Layer', 'training_epochs':max(50,min(int(epochs),1000)), 'predictions':rows}
