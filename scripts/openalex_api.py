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
            "per_page": min(limit, 25),  # OpenAlex 最大25
            "filter": "has_works:true"  # 只返回有论文的学者
        }
        
        data = self._get("authors", params)
        results = []
        
        for item in data.get("results", []):
            results.append({
                "id": item.get("id", "").split("/")[-1] if item.get("id") else None,
                "name": item.get("display_name", "Unknown"),
                "orcid": item.get("orcid", ""),
                "works_count": item.get("works_count", 0),
                "cited_by_count": item.get("cited_by_count", 0),
                "h_index": item.get("summary_stats", {}).get("h_index", 0) if item.get("summary_stats") else 0,
                "institutions": [inst.get("display_name") for inst in item.get("last_known_institutions", [])],
                "topics": [topic.get("display_name") for topic in item.get("topics", [])[:5]],
                "openalex_url": item.get("id", "")
            })
        
        return results
    
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
                "h_index": data.get("summary_stats", {}).get("h_index", 0) if data.get("summary_stats") else 0,
                "i10_index": data.get("summary_stats", {}).get("i10_index", 0) if data.get("summary_stats") else 0,
                "institutions": [inst.get("display_name") for inst in data.get("last_known_institutions", [])],
                "topics": [topic.get("display_name") for topic in data.get("topics", [])[:10]],
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
                "open_access": item.get("open_access", {}).get("is_oa", False),
                "venue": item.get("primary_location", {}).get("source", {}).get("display_name") if item.get("primary_location") else None
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
                "country": item.get("geo", {}).get("country", "Unknown") if item.get("geo") else "Unknown",
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
                "h_index": item.get("summary_stats", {}).get("h_index", 0) if item.get("summary_stats") else 0
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
