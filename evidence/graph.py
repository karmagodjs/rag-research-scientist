
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class EvidenceGraph:

    def __init__(self):
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        self._node_ids = set()

    def add_node(self, node_id: str, label: str, node_type: str, metadata: Dict[str, Any] = None):
        if node_id not in self._node_ids:
            self._node_ids.add(node_id)
            self.nodes.append({
                "id": node_id,
                "label": label,
                "type": node_type,  

                "metadata": metadata or {}
            })

    def add_edge(self, source: str, target: str, relation: str):
        self.edges.append({
            "source": source,
            "target": target,
            "relation": relation
        })

    def build_graph(
        self,
        query: str,
        claims: List[Dict[str, Any]],
        contradictions: List[Dict[str, Any]],
        documents: List[Any]
    ) -> Dict[str, Any]:

        q_id = "query_root"
        self.add_node(q_id, query, "question")


        for doc in documents:
            doc_id = doc.id if hasattr(doc, "id") else doc["id"]
            title = doc.title if hasattr(doc, "title") else doc["title"]
            url = doc.url if hasattr(doc, "url") else doc.get("url", "")
            self.add_node(doc_id, title, "paper", {"url": url})
            self.add_edge(q_id, doc_id, "retrieved_paper")


        for idx, claim in enumerate(claims):
            claim_id = f"claim_{idx+1}"
            self.add_node(claim_id, claim["claim"], "claim", {"confidence": claim.get("confidence", 0.0)})
            self.add_edge(q_id, claim_id, "evaluates_claim")

            for ev in claim.get("evidence", []):
                ev_id = f"ev_{abs(hash(ev['snippet']))}"
                self.add_node(ev_id, ev["snippet"][:50] + "...", "evidence", {"source_url": ev["source_url"]})
                self.add_edge(claim_id, ev_id, "has_evidence")
                self.add_edge(ev["paper_id"], ev_id, "provides_evidence")


        for contra in contradictions:
            c_text = contra["claim"]
            for c_node in self.nodes:
                if c_node["label"] == c_text:
                    for s_ev in contra.get("supporting_evidence", []):
                        self.add_edge(c_node["id"], s_ev["paper_id"], "supports")
                    for c_ev in contra.get("contradicting_evidence", []):
                        self.add_edge(c_node["id"], c_ev["paper_id"], "contradicts")

        logger.info(f"Built Evidence Graph with {len(self.nodes)} nodes and {len(self.edges)} edges.")
        return {
            "nodes": self.nodes,
            "edges": self.edges
        }

    def to_networkx(self):
        try:
            import networkx as nx
            G = nx.DiGraph()
            for node in self.nodes:
                G.add_node(node["id"], label=node["label"], type=node["type"], **node["metadata"])
            for edge in self.edges:
                G.add_edge(edge["source"], edge["target"], relation=edge["relation"])
            return G
        except ImportError:
            logger.info("NetworkX not installed; skipping networkx conversion.")
            return None
