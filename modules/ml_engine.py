import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from data.career_tracks import CAREER_TRACKS
import sqlite3

# KMeans clustering for career archetypes
def get_career_clusters(n_clusters=3):
    X = np.array([c['features'] for c in CAREER_TRACKS])
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    clusters = {}
    for idx, label in enumerate(labels):
        clusters.setdefault(label, []).append(CAREER_TRACKS[idx]['name'])
    return clusters, kmeans.cluster_centers_

# Recommend top 3 careers for a user_id
def recommend_careers(user_id):
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT analytical, creativity, engineering, communication, curiosity FROM quiz_scores WHERE user_id=?', (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None, None
    user_vec = np.array(row).reshape(1, -1)
    career_vecs = np.array([c['features'] for c in CAREER_TRACKS])
    similarities = cosine_similarity(user_vec, career_vecs)[0]
    ranked = sorted(zip(CAREER_TRACKS, similarities), key=lambda x: x[1], reverse=True)
    top3 = [(c['name'], float(sim)) for c, sim in ranked[:3]]
    return top3, similarities
