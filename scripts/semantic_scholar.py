#!/usr/bin/env python3
"""
AI人才图谱 v2 - Semantic Scholar API 封装（内置版）
"""
import requests
import sys
import time
from typing import List, Dict, Optional

SS_BASE = "https://api.semanticscholar.org/graph/v1"

class SemanticScholarAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "AI-Talent-Graph/2.0"})
        self.last_request_time = 0
        self.min_interval = 1.0  # 保守限速 1s

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

    def search_authors(self, query: str, limit: int = 5) -> List[Dict]:
        self._rate_limit()
        try:
            r = self.session.get(
                f"{SS_BASE}/author/search",
                params={"query": query, "limit": min(limit, 10),
                        "fields": "name,affiliations,hIndex,citationCount,paperCount,authorId"},
                timeout=30
            )
            r.raise_for_status()
            return r.json().get("data", [])
        except Exception as e:
            print(f"Semantic Scholar 搜索失败: {e}", file=sys.stderr)
            return []
