import os
import sys
import json
import uuid

# Add parent directory to Python path for Vercel Serverless Function imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler
from agent import ResearchAgent, AgentConfig


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
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode('utf-8')) if post_data else {}
            query = data.get('query', 'OCR on low-resource Indic languages since 2024')
            max_papers = int(data.get('max_papers', 10))
            iterations = int(data.get('iterations', 1))

            config = AgentConfig(max_papers=max_papers, max_iterations=iterations)
            agent = ResearchAgent(config=config)
            report = agent.run(query)
            report['id'] = f"res_{uuid.uuid4().hex[:8]}"

            self._send_json(report, status=200)
            return
        except Exception as e:
            self._send_json({'error': str(e)}, status=500)
            return

    def do_GET(self):
        self._send_json({
            'status': 'RAG Research Scientist Serverless API is online.',
            'version': '1.0.0'
        }, status=200)
