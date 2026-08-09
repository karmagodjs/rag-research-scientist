#!/usr/bin/env python3
"""
Lightweight Web Dashboard Server for RAG Research Scientist Agent.
Implements REST API endpoints for research execution, evidence graph retrieval, and static web serving.
"""

import http.server
import socketserver
import os
import json
import uuid
import logging
from typing import Dict, Any
from agent import ResearchAgent, AgentConfig

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")

# In-memory store for research runs
RESEARCH_STORE: Dict[str, Dict[str, Any]] = {}

logger = logging.getLogger("ResearchServer")


class ResearchHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _send_json(self, data: Any, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_POST(self):
        """Handle POST /api/research requests to trigger research agent."""
        if self.path == "/api/research":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8"))
                query = data.get("query", "OCR on low-resource Indic languages since 2024")
                max_papers = int(data.get("max_papers", 15))
                iterations = int(data.get("iterations", 1))

                research_id = f"res_{uuid.uuid4().hex[:8]}"
                config = AgentConfig(max_papers=max_papers, max_iterations=iterations)
                agent = ResearchAgent(config=config)
                
                report = agent.run(query)
                report["id"] = research_id
                RESEARCH_STORE[research_id] = report

                self._send_json(report, status=201)
                return
            except Exception as e:
                logger.error(f"Error executing research pipeline: {str(e)}")
                self._send_json({"error": str(e)}, status=500)
                return

        self._send_json({"error": "Endpoint not found"}, status=404)

    def do_GET(self):
        """Handle GET requests for static files and REST API endpoints."""
        path = self.path

        # REST API Routes
        if path.startswith("/api/research"):
            parts = path.strip("/").split("/")  # ['api', 'research', ':id', ':sub']
            if len(parts) == 3:  # GET /api/research/:id
                research_id = parts[2]
                report = RESEARCH_STORE.get(research_id)
                if report:
                    self._send_json(report)
                else:
                    self._send_json({"error": "Research ID not found"}, status=404)
                return

            elif len(parts) == 4:  # GET /api/research/:id/:sub
                research_id = parts[2]
                sub = parts[3]
                report = RESEARCH_STORE.get(research_id)
                if not report:
                    self._send_json({"error": "Research ID not found"}, status=404)
                    return

                if sub == "claims":
                    self._send_json(report.get("claims", []))
                elif sub == "evidence":
                    all_ev = [ev for c in report.get("claims", []) for ev in c.get("evidence", [])]
                    self._send_json(all_ev)
                elif sub == "graph":
                    self._send_json(report.get("evidence_graph", {}))
                elif sub == "papers":
                    self._send_json(report.get("citation_list", []))
                elif sub == "gaps":
                    self._send_json({
                        "gaps": report.get("open_research_gaps", []),
                        "recommendations": report.get("what_to_research_next", [])
                    })
                else:
                    self._send_json({"error": f"Invalid sub-resource {sub}"}, status=404)
                return

        # Serve static web files
        super().do_GET()


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    print(f"[*] Starting RAG Research Scientist Server on http://localhost:{PORT}")
    print(f"[*] API Endpoints:")
    print(f"    POST /api/research")
    print(f"    GET  /api/research/:id")
    print(f"    GET  /api/research/:id/claims")
    print(f"    GET  /api/research/:id/evidence")
    print(f"    GET  /api/research/:id/graph")
    print(f"    GET  /api/research/:id/papers")
    print(f"    GET  /api/research/:id/gaps")
    print(f"[*] Web UI serving from: {WEB_DIR}\n")

    with ReusableTCPServer(("", PORT), ResearchHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Shutting down server.")


if __name__ == "__main__":
    main()
