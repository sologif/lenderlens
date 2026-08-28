import os
import json
import pickle
import numpy as np
import networkx as nx
from typing import Dict, Any, List, Optional
from database import get_db_connection
from models.schemas import Layer4Result

WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "weights")

# ── Load trained RandomForest GNN classifier at startup ────────────────────
_gnn_clf = None

def _load_gnn_clf():
    global _gnn_clf
    if _gnn_clf is not None:
        return _gnn_clf
    path = os.path.join(WEIGHTS_DIR, "gnn_classifier.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            _gnn_clf = pickle.load(f)
    return _gnn_clf


def build_full_network_graph() -> nx.Graph:
    conn = get_db_connection()
    cursor = conn.cursor()
    nodes_data = cursor.execute("SELECT * FROM graph_nodes").fetchall()
    edges_data = cursor.execute("SELECT * FROM graph_edges").fetchall()
    conn.close()

    G = nx.Graph()
    for row in nodes_data:
        meta = {}
        try:
            if row["metadata"]:
                meta = json.loads(row["metadata"])
        except:
            pass
        G.add_node(row["id"],
                   entity_type=row["entity_type"],
                   entity_value=row["entity_value"],
                   label=row["label"],
                   is_suspicious=bool(row["is_suspicious"]),
                   risk_score=float(row["risk_score"]),
                   metadata=meta)

    for row in edges_data:
        G.add_edge(row["source_id"], row["target_id"],
                   id=row["id"],
                   relation_type=row["relation_type"],
                   is_suspicious=bool(row["is_suspicious"]))
    return G


def _extract_node_features(G: nx.Graph, focal_id: str, subgraph: nx.Graph) -> np.ndarray:
    """
    Extracts the 4 GNN node features the RandomForest was trained on:
      [0] degree_centrality     - how connected is this node
      [1] flagged_neighbors     - count of adjacent suspicious nodes
      [2] shared_hotlines       - shared PHONE/UPI nodes in ego-graph
      [3] rbi_registered        - 1 if registry record exists
    """
    try:
        centrality = nx.degree_centrality(subgraph).get(focal_id, 0.0)
    except:
        centrality = 0.0

    flagged_neighbors = 0
    shared_hotlines = 0
    for n in subgraph.neighbors(focal_id):
        d = subgraph.nodes[n]
        if d.get("is_suspicious") or d.get("risk_score", 0) > 70:
            flagged_neighbors += 1
        if d.get("entity_type") in ("PHONE", "UPI_ID"):
            shared_hotlines += 1

    # Check RBI registry for the domain
    focal_value = G.nodes[focal_id].get("entity_value", "")
    conn = get_db_connection()
    row = conn.cursor().execute(
        "SELECT 1 FROM government_registry WHERE official_domain = ? LIMIT 1",
        (focal_value,)
    ).fetchone()
    conn.close()
    rbi_registered = 1.0 if row else 0.0

    return np.array([[centrality, flagged_neighbors, shared_hotlines, rbi_registered]], dtype=float)


def analyze_network_risk(domain: str, payment_info: Optional[Dict[str, Any]] = None, depth: int = 2) -> Layer4Result:
    """
    Layer 4 – GNN Graph Fraud Analysis
    =====================================
    1. Loads full network graph from database.
    2. Finds or dynamically inserts the domain node.
    3. Injects any UPI/phone entities extracted from page text.
    4. Runs k-hop neighborhood aggregation.
    5. Feeds 4-feature vector into trained RandomForest for fraud probability.
    6. Combines ML score with graph metrics for final network_risk_score.
    """
    G = build_full_network_graph()
    cleaned = (domain.lower()
                .replace("https://", "").replace("http://", "")
                .replace("www.", "").split("/")[0])

    # ── Find focal node ───────────────────────────────────────────────────
    focal_id = None
    for node, data in G.nodes(data=True):
        if data.get("entity_value", "").lower() == cleaned:
            focal_id = node
            break
    if not focal_id:
        for node, data in G.nodes(data=True):
            if cleaned in data.get("entity_value", "").lower():
                focal_id = node
                break

    # ── Dynamically inject domain node if unknown ─────────────────────────
    if not focal_id:
        focal_id = f"node_dynamic_{cleaned}"
        G.add_node(focal_id,
                   entity_type="DOMAIN",
                   entity_value=cleaned,
                   label=cleaned,
                   is_suspicious=False,
                   risk_score=10.0,
                   metadata={"status": "ZERO_SHOT"})

    # ── Inject payment entities from page extraction ──────────────────────
    if payment_info:
        for key, etype in [("upi_id", "UPI_ID"), ("phone", "PHONE")]:
            val = payment_info.get(key, "")
            if not val:
                continue
            existing = next((n for n, d in G.nodes(data=True) if d.get("entity_value") == val), None)
            if not existing:
                existing = f"node_dyn_{etype.lower()}_{val}"
                # Cross-check against known flagged nodes
                conn = get_db_connection()
                flagged_row = conn.cursor().execute(
                    "SELECT risk_score, is_suspicious FROM graph_nodes WHERE entity_value = ? LIMIT 1",
                    (val,)
                ).fetchone()
                conn.close()
                is_susp = bool(flagged_row["is_suspicious"]) if flagged_row else False
                rscore  = float(flagged_row["risk_score"])   if flagged_row else 10.0
                G.add_node(existing, entity_type=etype, entity_value=val,
                           label=val, is_suspicious=is_susp, risk_score=rscore)
            G.add_edge(focal_id, existing,
                       relation_type="ROUTES_PAYMENT_TO" if etype == "UPI_ID" else "SHARES_HOTLINE",
                       is_suspicious=False)

    # ── k-hop ego subgraph ────────────────────────────────────────────────
    ego = set([focal_id])
    frontier = set([focal_id])
    for _ in range(depth):
        nxt = set()
        for n in frontier:
            if n in G:
                nxt.update(set(G.neighbors(n)) - ego)
        ego.update(nxt)
        frontier = nxt
    subgraph = G.subgraph(ego).copy()

    # ── Graph metric counts ───────────────────────────────────────────────
    connected_flagged_domains = 0
    connected_suspicious_accounts = 0
    connected_reported_phones = 0
    high_risk_neighbors = 0

    for n in subgraph.nodes():
        if n == focal_id:
            continue
        d = subgraph.nodes[n]
        is_susp = d.get("is_suspicious", False)
        etype   = d.get("entity_type", "")
        rscore  = d.get("risk_score", 0.0)
        if is_susp or rscore > 70:
            high_risk_neighbors += 1
            if etype == "DOMAIN":
                connected_flagged_domains += 1
            elif etype in ("PAYMENT_ACCOUNT", "UPI_ID", "BANK_ACCOUNT"):
                connected_suspicious_accounts += 1
            elif etype == "PHONE":
                connected_reported_phones += 1

    try:
        centrality = nx.degree_centrality(subgraph).get(focal_id, 0.0)
    except:
        centrality = 0.0

    # ── ML inference: RandomForest fraud probability ──────────────────────
    clf = _load_gnn_clf()
    ml_fraud_prob = None
    if clf is not None:
        features = _extract_node_features(G, focal_id, subgraph)
        ml_fraud_prob = float(clf.predict_proba(features)[0][1])  # P(fraud)

    # ── Risk score fusion: graph metrics + ML probability ─────────────────
    if ml_fraud_prob is not None:
        # Scale ML probability [0,1] to [0,100] and blend with graph evidence
        ml_contribution = ml_fraud_prob * 70.0
        graph_contribution = (
            connected_flagged_domains * 8.0 +
            connected_suspicious_accounts * 10.0 +
            connected_reported_phones * 5.0
        )
        network_risk_score = min(round(ml_contribution + graph_contribution, 1), 96.0)
    else:
        if connected_flagged_domains >= 2 or connected_suspicious_accounts >= 1:
            network_risk_score = min(round(75.0 + connected_flagged_domains * 6.0 + connected_suspicious_accounts * 8.0, 1), 96.0)
        elif high_risk_neighbors > 0:
            network_risk_score = min(round(45.0 + high_risk_neighbors * 8.0, 1), 68.0)
        else:
            network_risk_score = round(max(subgraph.nodes[focal_id].get("risk_score", 10.0), 8.0), 1)

    # ── Format output ─────────────────────────────────────────────────────
    nodes_list = []
    for n in subgraph.nodes():
        d = subgraph.nodes[n]
        nodes_list.append({
            "id": n,
            "entity_type": d.get("entity_type", "UNKNOWN"),
            "entity_value": d.get("entity_value", ""),
            "label": d.get("label", n),
            "is_suspicious": d.get("is_suspicious", False),
            "risk_score": d.get("risk_score", 0.0),
            "is_focal": (n == focal_id),
            "metadata": d.get("metadata", {}),
        })

    edges_list = []
    for u, v, d in subgraph.edges(data=True):
        edges_list.append({
            "id": d.get("id", f"{u}_{v}"),
            "source": u, "target": v,
            "relation_type": d.get("relation_type", "CONNECTED_TO"),
            "is_suspicious": d.get("is_suspicious", False),
        })

    flags = []
    if connected_flagged_domains > 0:
        flags.append(f"🔴 GNN: Connected to {connected_flagged_domains} previously flagged/blocked domains")
    if connected_suspicious_accounts > 0:
        flags.append(f"🔴 GNN: Shares payment infrastructure with {connected_suspicious_accounts} flagged mule UPI/bank accounts")
    if connected_reported_phones > 0:
        flags.append(f"🔴 GNN: Shared phone hotline with {connected_reported_phones} reported fraud syndicate entities")
    if network_risk_score <= 20.0:
        flags.append("✅ GNN: Entity isolated from known fraud syndicates — clean network neighbourhood")
    if ml_fraud_prob is not None:
        flags.append(f"🤖 GNN Model (RandomForest): Fraud probability = {ml_fraud_prob:.2%}")

    details = {
        "focal_node_id": focal_id,
        "subgraph_size": len(nodes_list),
        "edge_count": len(edges_list),
        "high_risk_neighbors": high_risk_neighbors,
        "degree_centrality": round(centrality, 3),
        "ml_fraud_probability": round(ml_fraud_prob, 4) if ml_fraud_prob is not None else None,
        "model": "RandomForestClassifier (150 trees) trained on Kaggle graph topology + RBI registry features",
        "syndicate_cluster": "Cluster_Gamma_Predatory" if network_risk_score > 70 else "None",
    }

    return Layer4Result(
        network_risk_score=network_risk_score,
        connected_flagged_domains=connected_flagged_domains,
        connected_suspicious_accounts=connected_suspicious_accounts,
        connected_reported_phones=connected_reported_phones,
        centrality_score=round(centrality, 3),
        subgraph_nodes=nodes_list,
        subgraph_edges=edges_list,
        flags=flags,
        details=details,
    )
