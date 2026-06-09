import heapq
import pickle
import os
import numpy as np
import pandas as pd
import networkx as nx
from sklearn.neighbors import NearestNeighbors


def build_mood_graph(df: pd.DataFrame, k: int = 10) -> nx.DiGraph:
    print(f'Building mood graph for {len(df)} Bollywood tracks (k={k})...')

    coords = df[['valence', 'energy']].values

    knn = NearestNeighbors(n_neighbors=k + 1, metric='euclidean')
    knn.fit(coords)
    distances, indices = knn.kneighbors(coords)

    G = nx.DiGraph()

    for _, row in df.iterrows():
        G.add_node(row['id'],
            valence     = float(row['valence']),
            energy      = float(row['energy']),
            name        = str(row['name']),
            artist      = str(row['artist']),
            preview_url = row.get('preview_url'),
            album_image = row.get('album_image'),
        )

    for i in range(len(df)):
        src = df.iloc[i]['id']
        for j, dist in zip(indices[i][1:], distances[i][1:]):
            tgt = df.iloc[j]['id']
            G.add_edge(src, tgt, weight=float(dist))

    print(f'Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')
    return G


def find_nearest_node(G: nx.DiGraph, valence: float, energy: float) -> str:
    best, best_d = None, float('inf')
    for node, attrs in G.nodes(data=True):
        d = ((attrs['valence'] - valence) ** 2 +
             (attrs['energy']  - energy)  ** 2) ** 0.5
        if d < best_d:
            best_d, best = d, node
    return best


def find_journey(
    G: nx.DiGraph,
    start_valence: float, start_energy: float,
    target_valence: float, target_energy: float,
    n_songs: int = 8
) -> list:
    start = find_nearest_node(G, start_valence, start_energy)
    end   = find_nearest_node(G, target_valence, target_energy)

    def h(node):
        a = G.nodes[node]
        return ((a['valence'] - target_valence) ** 2 +
                (a['energy']  - target_energy)  ** 2) ** 0.5

    heap    = [(0 + h(start), 0.0, start, [start])]
    visited = set()

    while heap:
        f, g, cur, path = heapq.heappop(heap)
        if cur in visited:
            continue
        visited.add(cur)

        if len(path) >= n_songs or cur == end:
            return [{
                'id':          node,
                'name':        G.nodes[node]['name'],
                'artist':      G.nodes[node]['artist'],
                'valence':     G.nodes[node]['valence'],
                'energy':      G.nodes[node]['energy'],
                'preview_url': G.nodes[node]['preview_url'],
                'album_image': G.nodes[node]['album_image'],
                'position':    i
            } for i, node in enumerate(path)]

        for nbr in G.neighbors(cur):
            if nbr not in visited:
                ng = g + G[cur][nbr]['weight']
                heapq.heappush(heap, (ng + h(nbr), ng, nbr, path + [nbr]))

    return []


if __name__ == '__main__':
    df = pd.read_parquet('data/tracks.parquet')
    G  = build_mood_graph(df, k=10)

    os.makedirs('models', exist_ok=True)
    with open('models/mood_graph.pkl', 'wb') as f:
        pickle.dump(G, f)
    print('Saved to models/mood_graph.pkl')

    journey = find_journey(G, 0.15, 0.20, 0.85, 0.80, n_songs=8)
    print()
    print('Udaas -> Khushi journey:')
    for s in journey:
        print(f"  {s['position']+1}. {s['name'][:40]:40s}"
              f" val={s['valence']:.2f} nrg={s['energy']:.2f}")