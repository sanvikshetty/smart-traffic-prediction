import torch
from torch import nn
from torch_geometric.nn import GCNConv

class TrafficGCN(nn.Module):
    def __init__(self, in_channels=4, hidden=32):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden)
        self.conv2 = GCNConv(hidden, hidden)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index).relu()
        return self.head(x).squeeze(-1)
