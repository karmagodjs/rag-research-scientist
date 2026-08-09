"""
Persistent Storage module for RAG Research Scientist Agent.
Supports Vercel KV / Upstash Redis REST API, persistent file storage fallback, and in-memory caching.
"""

import os
import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global fallback in-memory store
_IN_MEMORY_STORE: Dict[str, Dict[str, Any]] = {}
_LOCAL_FILE_DIR = os.getenv("STORAGE_DIR", os.path.join(os.path.dirname(__file__), ".storage"))


class PersistentStorage:
    """Unified storage interface supporting Vercel KV / Redis, local disk, and in-memory fallbacks."""

    def __init__(self):
        self.kv_url = os.getenv("KV_REST_API_URL") or os.getenv("UPSTASH_REDIS_REST_URL")
        self.kv_token = os.getenv("KV_REST_API_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN")
        self.has_kv = bool(self.kv_url and self.kv_token)

        if self.has_kv:
            logger.info("PersistentStorage initialized with Vercel KV / Upstash Redis REST API.")
        else:
            logger.info("PersistentStorage operating with local disk / in-memory fallback.")
            try:
                os.makedirs(_LOCAL_FILE_DIR, exist_ok=True)
            except Exception:
                pass

    def save(self, research_id: str, data: Dict[str, Any]) -> bool:
        """Save research report by ID."""
        _IN_MEMORY_STORE[research_id] = data

        if self.has_kv:
            try:
                url = f"{self.kv_url.rstrip('/')}/set/{urllib.parse.quote(research_id)}"
                payload = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {self.kv_token}",
                        "Content-Type": "application/json"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status in (200, 201):
                        return True
            except Exception as e:
                logger.warning(f"Failed to save to Vercel KV: {e}. Saved to fallback store.")

        # Local disk fallback
        try:
            file_path = os.path.join(_LOCAL_FILE_DIR, f"{research_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to save to disk fallback: {e}")

        return True

    def get(self, research_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve research report by ID."""
        if research_id in _IN_MEMORY_STORE:
            return _IN_MEMORY_STORE[research_id]

        if self.has_kv:
            try:
                url = f"{self.kv_url.rstrip('/')}/get/{urllib.parse.quote(research_id)}"
                req = urllib.request.Request(
                    url,
                    headers={"Authorization": f"Bearer {self.kv_token}"},
                    method="GET"
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        res = json.loads(resp.read().decode('utf-8'))
                        result = res.get("result")
                        if result:
                            if isinstance(result, str):
                                data = json.loads(result)
                            else:
                                data = result
                            _IN_MEMORY_STORE[research_id] = data
                            return data
            except Exception as e:
                logger.warning(f"Failed to fetch from Vercel KV: {e}")

        # Local disk fallback
        try:
            file_path = os.path.join(_LOCAL_FILE_DIR, f"{research_id}.json")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    _IN_MEMORY_STORE[research_id] = data
                    return data
        except Exception as e:
            logger.warning(f"Failed to fetch from disk fallback: {e}")

        return None


storage = PersistentStorage()
