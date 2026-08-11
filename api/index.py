import os
import sys
import json
import uuid
import logging
from urllib.parse import urlparse

# Add parent directory to Python path for Vercel Serverless Function imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler
from agent import ResearchAgent, AgentConfig
from storage import storage

logger = logging.getLogger("VercelAPI")


class handler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if '/research' in path or '/api' in path or path in ['', '/', '/api/index.py']:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b''
            try:
                data = json.loads(post_data.decode('utf-8')) if post_data else {}
                query = data.get('query', 'OCR on low-resource Indic languages since 2024')
                max_papers = min(int(data.get('max_papers', 10)), 15)
                # Cap iterations to 1 and timeout to 5s in serverless environment to prevent function timeout
                iterations = 1 if os.getenv('VERCEL') else min(int(data.get('iterations', 1)), 2)

                config = AgentConfig(
                    max_papers=max_papers,
                    max_iterations=iterations,
                    timeout_seconds=5
                )
                agent = ResearchAgent(config=config)
                report = agent.run(query)

                research_id = f"res_{uuid.uuid4().hex[:8]}"
                report['id'] = research_id
                storage.save(research_id, report)

                self._send_json(report, status=201)
                return
            except Exception as e:
                logger.exception(f"Error executing research pipeline: {e}")
                self._send_json({'error': 'An internal server error occurred while processing research request.'}, status=500)
                return

        self._send_json({'error': 'Endpoint not found'}, status=404)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path.startswith("/api/research"):
            parts = path.strip("/").split("/")  # ['api', 'research', ':id', ':sub']
            if len(parts) == 3:  # GET /api/research/:id
                research_id = parts[2]
                report = storage.get(research_id)
                if report:
                    self._send_json(report)
                else:
                    self._send_json({"error": "Research ID not found"}, status=404)
                return

            elif len(parts) == 4:  # GET /api/research/:id/:sub
                research_id = parts[2]
                sub = parts[3]
                report = storage.get(research_id)
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

        self._send_json({
            'status': 'RAG Research Scientist Serverless API is online.',
            'version': '1.0.0'
        }, status=200)
