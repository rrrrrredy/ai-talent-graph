#!/usr/bin/env python3
"""
OpenAlex API 封装模块
完全免费，无需注册，合理频率使用
https://docs.openalex.org/
"""

import requests
import json
import time
from typing import List, Dict, Optional

OPENALEX_BASE = "https://api.openalex.org"

class OpenAlexAPI:
    """OpenAlex API 封装"""
    
    def __init__(self, email: Optional[str] = None):
        """
        初始化
        
        Args:
            email: 可选，用于 polite pool（推荐）
        """
        self.session = requests.Session()
        self.email = email
        self.last_request_time = 0
        self.min_interval = 0.1  # 100ms 间隔，约10请求/秒

    @staticmethod
    def _dict(value) -> Dict:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _list(value) -> List:
        return value if isinstance(value, list) else []
    
    def _rate_limit(self):
        """频率限制"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """GET 请求"""
        self._rate_limit()
        
        headers = {"User-Agent": "AI-Talent-Graph/1.0"}
        if self.email:
            headers["mailto"] = self.email
        
        url = f"{OPENALEX_BASE}/{endpoint}"
        resp = self.session.get(url, params=params, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception(f"OpenAlex API error: {resp.status_code} - {resp.text}")
    
    def search_authors(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索学者
        
        Args:
            query: 搜索关键词（姓名/机构/研究方向）
            limit: 返回结果数量
        
        Returns:
            学者列表
        """
        params = {
            "search": query,
            "per_page": min(limit, 25)  # OpenAlex 最大25
        }
        
        data = self._get("authors", params)
        results = []
        
        for item in data.get("results", []):
            if (item.get("works_count") or 0) <= 0:
                continue
            results.append({
                "id": item.get("id", "").split("/")[-1] if item.get("id") else None,
                "name": item.get("display_name", "Unknown"),
                "orcid": item.get("orcid", ""),
                "works_count": item.get("works_count", 0),
                "cited_by_count": item.get("cited_by_count", 0),
                "h_index": self._dict(item.get("summary_stats")).get("h_index", 0),
                "institutions": [inst.get("display_name") for inst in self._list(item.get("last_known_institutions"))],
                "topics": [topic.get("display_name") for topic in self._list(item.get("topics"))[:5]],
                "openalex_url": item.get("id", "")
            })
        
        return results

    def search_authors_by_works(self, query: str, limit: int = 10) -> List[Dict]:
        """
        通过论文主题搜索学者。

        OpenAlex author search is name-centric and can return noisy pseudo-author
        records for broad research topics. For topic queries, search works first
        and aggregate real authors from authorships.
        """
        params = {
            "filter": f"title.search:{query}",
            "per_page": min(max(limit * 12, 20), 50)
        }

        data = self._get("works", params)
        authors = {}

        total_results = len(data.get("results", []))
        for idx, work in enumerate(data.get("results", [])):
            title = work.get("display_name") or "Unknown"
            year = work.get("publication_year")
            cited_by = work.get("cited_by_count") or 0
            relevance_score = max(total_results - idx, 1)

            for authorship in self._list(work.get("authorships"))[:8]:
                author = self._dict(authorship.get("author"))
                author_id = author.get("id", "")
                name = author.get("display_name")
                if not author_id or not name:
                    continue

                short_id = author_id.split("/")[-1]
                entry = authors.setdefault(short_id, {
                    "id": short_id,
                    "name": name,
                    "orcid": None,
                    "works_count": 0,
                    "cited_by_count": 0,
                    "h_index": 0,
                    "institutions": [],
                    "topics": [],
                    "openalex_url": author_id,
                    "matched_works_count": 0,
                    "matched_relevance_score": 0,
                    "matched_citations": 0,
                    "matched_works": []
                })

                entry["matched_works_count"] += 1
                entry["matched_relevance_score"] += relevance_score
                entry["matched_citations"] += cited_by
                if len(entry["matched_works"]) < 3:
                    entry["matched_works"].append({
                        "title": title[:120],
                        "year": year,
                        "cited_by_count": cited_by
                    })

                for inst in self._list(authorship.get("institutions")):
                    inst_name = inst.get("display_name")
                    if inst_name and inst_name not in entry["institutions"]:
                        entry["institutions"].append(inst_name)

        ranked = sorted(
            authors.values(),
            key=lambda item: (
                item["matched_works_count"],
                item["matched_relevance_score"],
                item["matched_citations"]
            ),
            reverse=True
        )

        enriched = []
        for entry in ranked[:limit]:
            detail = self.get_author(entry["id"])
            if detail:
                entry.update({
                    "orcid": detail.get("orcid"),
                    "works_count": detail.get("works_count", entry["works_count"]),
                    "cited_by_count": detail.get("cited_by_count", entry["cited_by_count"]),
                    "h_index": detail.get("h_index", entry["h_index"]),
                    "institutions": detail.get("institutions") or entry["institutions"],
                    "topics": detail.get("topics") or entry["topics"],
                    "openalex_url": detail.get("openalex_url") or entry["openalex_url"]
                })
            enriched.append(entry)

        return enriched
    
    def get_author(self, author_id: str) -> Optional[Dict]:
        """
        获取学者详情
        
        Args:
            author_id: OpenAlex ID (如 A123456789)
        
        Returns:
            学者详情
        """
        try:
            data = self._get(f"authors/{author_id}")
            
            return {
                "id": author_id,
                "name": data.get("display_name", "Unknown"),
                "orcid": data.get("orcid", ""),
                "works_count": data.get("works_count", 0),
                "cited_by_count": data.get("cited_by_count", 0),
                "h_index": self._dict(data.get("summary_stats")).get("h_index", 0),
                "i10_index": self._dict(data.get("summary_stats")).get("i10_index", 0),
                "institutions": [inst.get("display_name") for inst in self._list(data.get("last_known_institutions"))],
                "topics": [topic.get("display_name") for topic in self._list(data.get("topics"))[:10]],
                "counts_by_year": data.get("counts_by_year", []),
                "openalex_url": data.get("id", "")
            }
        except Exception as e:
            print(f"获取学者详情失败: {e}")
            return None
    
    def get_author_works(self, author_id: str, limit: int = 10) -> List[Dict]:
        """
        获取学者论文列表
        
        Args:
            author_id: OpenAlex ID
            limit: 返回数量
        
        Returns:
            论文列表
        """
        params = {
            "filter": f"author.id:{author_id}",
            "per_page": min(limit, 25),
            "sort": "cited_by_count:desc"
        }
        
        data = self._get("works", params)
        results = []
        
        for item in data.get("results", []):
            results.append({
                "id": item.get("id", "").split("/")[-1] if item.get("id") else None,
                "title": item.get("display_name", "Unknown"),
                "publication_year": item.get("publication_year"),
                "cited_by_count": item.get("cited_by_count", 0),
                "type": item.get("type"),
                "open_access": self._dict(item.get("open_access")).get("is_oa", False),
                "venue": self._dict(self._dict(item.get("primary_location")).get("source")).get("display_name")
            })
        
        return results
    
    def search_institution(self, name: str) -> List[Dict]:
        """
        搜索机构
        
        Args:
            name: 机构名称
        
        Returns:
            机构列表
        """
        params = {
            "search": name,
            "per_page": 5
        }
        
        data = self._get("institutions", params)
        results = []
        
        for item in data.get("results", []):
            results.append({
                "id": item.get("id", "").split("/")[-1] if item.get("id") else None,
                "name": item.get("display_name", "Unknown"),
                "country": self._dict(item.get("geo")).get("country", "Unknown"),
                "works_count": item.get("works_count", 0),
                "cited_by_count": item.get("cited_by_count", 0),
                "openalex_url": item.get("id", "")
            })
        
        return results
    
    def get_institution_authors(self, institution_id: str, limit: int = 20) -> List[Dict]:
        """
        获取机构学者列表
        
        Args:
            institution_id: 机构ID
            limit: 返回数量
        
        Returns:
            学者列表
        """
        params = {
            "filter": f"last_known_institutions.id:{institution_id}",
            "per_page": min(limit, 25),
            "sort": "cited_by_count:desc"
        }
        
        data = self._get("authors", params)
        results = []
        
        for item in data.get("results", []):
            results.append({
                "id": item.get("id", "").split("/")[-1] if item.get("id") else None,
                "name": item.get("display_name", "Unknown"),
                "works_count": item.get("works_count", 0),
                "cited_by_count": item.get("cited_by_count", 0),
                "h_index": self._dict(item.get("summary_stats")).get("h_index", 0)
            })
        
        return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--type", choices=["author", "institution"], default="author", help="搜索类型")
    parser.add_argument("--limit", type=int, default=10, help="结果数量")
    args = parser.parse_args()
    
    api = OpenAlexAPI()
    
    if args.type == "author":
        results = api.search_authors(args.query, limit=args.limit)
    else:
        results = api.search_institution(args.query)
    
    print(json.dumps(results, ensure_ascii=False, indent=2))
