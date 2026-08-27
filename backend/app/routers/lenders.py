import json
from fastapi import APIRouter, HTTPException
from database import get_db_connection
from services.layer1_identity import verify_identity
from services.layer3_lstm import analyze_temporal_risk
from services.layer4_gnn import analyze_network_risk, build_full_network_graph

router = APIRouter(prefix="/api/lenders", tags=["Lenders"])

@router.get("")
def list_registered_lenders():
    """Lists all regulatory reference registry records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM government_registry ORDER BY legal_name ASC").fetchall()
    conn.close()

    return [dict(r) for r in rows]

@router.get("/{lender_id}/verification")
def get_lender_verification(lender_id: str):
    """Retrieves verification status and official regulatory data for a lender."""
    conn = get_db_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM government_registry WHERE lender_id = ?", (lender_id,)).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Lender record not found")

    return verify_identity(row["legal_name"], row["official_domain"])

@router.get("/{lender_id}/network")
def get_lender_network(lender_id: str):
    """Retrieves GNN network graph neighborhood for a lender."""
    conn = get_db_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT official_domain FROM government_registry WHERE lender_id = ?", (lender_id,)).fetchone()
    conn.close()

    domain = row["official_domain"] if row else lender_id
    return analyze_network_risk(domain=domain)

@router.get("/{lender_id}/timeline")
def get_lender_timeline(lender_id: str):
    """Retrieves LSTM temporal sequence activity for a lender."""
    conn = get_db_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT official_domain FROM government_registry WHERE lender_id = ?", (lender_id,)).fetchone()
    conn.close()

    domain = row["official_domain"] if row else lender_id
    return analyze_temporal_risk(domain=domain)

@router.get("/graph/global")
def get_global_network_graph():
    """Returns the entire fraud syndicate and reference network graph for the /network view."""
    conn = get_db_connection()
    cursor = conn.cursor()
    nodes_data = cursor.execute("SELECT * FROM graph_nodes").fetchall()
    edges_data = cursor.execute("SELECT * FROM graph_edges").fetchall()
    conn.close()

    nodes = []
    for r in nodes_data:
        meta = {}
        try:
            if r["metadata"]: meta = json.loads(r["metadata"])
        except:
            pass
        nodes.append({
            "id": r["id"],
            "entity_type": r["entity_type"],
            "entity_value": r["entity_value"],
            "label": r["label"],
            "is_suspicious": bool(r["is_suspicious"]),
            "risk_score": r["risk_score"],
            "metadata": meta
        })

    edges = []
    for r in edges_data:
        edges.append({
            "id": r["id"],
            "source": r["source_id"],
            "target": r["target_id"],
            "relation_type": r["relation_type"],
            "is_suspicious": bool(r["is_suspicious"])
        })

    return {"nodes": nodes, "edges": edges}
