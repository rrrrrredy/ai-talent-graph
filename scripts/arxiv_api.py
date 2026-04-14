#!/usr/bin/env python3
"""
arXiv API 封装模块
使用 OAI-PMH 和 arXiv API
https://info.arxiv.org/help/api/index.html
"""

import requests
import xml.etree.ElementTree as ET
import json
import time
from typing import List, Dict, Optional
from urllib.parse import quote

ARXIV_API_BASE = "http://export.arxiv.org/api/query"
ARXIV_OAI_BASE = "http://export.arxiv.org/oai2"

class ArxivAPI:
    """arXiv API 封装"""
    
    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_interval = 3  # arXiv 要求 3 秒间隔
    
    def _rate_limit(self):
        """频率限制"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def search(self, query: str, max_results: int = 10, sort_by: str = "relevance") -> List[Dict]:
        """
        搜索论文
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数（最大 300）
            sort_by: 排序方式 (relevance/lastUpdatedDate/submittedDate)
        
        Returns:
            论文列表
        """
        self._rate_limit()
        
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": min(max_results, 50),  # 限制50
            "sortBy": sort_by,
            "sortOrder": "descending"
        }
        
        try:
            resp = self.session.get(ARXIV_API_BASE, params=params, timeout=30)
            resp.raise_for_status()
            
            # 解析 XML
            root = ET.fromstring(resp.content)
            
            # 命名空间
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            results = []
            for entry in root.findall('atom:entry', ns):
                # 标题
                title = entry.find('atom:title', ns)
                title_text = title.text.strip() if title is not None and title.text else "Unknown"
                
                # 作者
                authors = []
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns)
                    if name is not None and name.text:
                        authors.append(name.text)
                
                # 摘要
                summary = entry.find('atom:summary', ns)
                summary_text = summary.text.strip() if summary is not None and summary.text else ""
                
                # 发表日期
                published = entry.find('atom:published', ns)
                published_date = published.text[:4] if published is not None and published.text else None
                
                # 更新日期
                updated = entry.find('atom:updated', ns)
                updated_date = updated.text[:10] if updated is not None and updated.text else None
                
                # arXiv ID
                id_elem = entry.find('atom:id', ns)
                arxiv_id = ""
                if id_elem is not None and id_elem.text:
                    # 提取 ID
                    parts = id_elem.text.split('/')
                    if len(parts) > 0:
                        arxiv_id = parts[-1].replace('abs/', '')
                
                # 分类
                categories = []
                for cat in entry.findall('atom:category', ns):
                    term = cat.get('term')
                    if term:
                        categories.append(term)
                
                # PDF 链接
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else ""
                
                results.append({
                    "arxiv_id": arxiv_id,
                    "title": title_text,
                    "authors": authors,
                    "abstract": summary_text[:200] + "..." if len(summary_text) > 200 else summary_text,
                    "published_year": int(published_date) if published_date and published_date.isdigit() else None,
                    "updated": updated_date,
                    "categories": categories,
                    "primary_category": categories[0] if categories else "",
                    "pdf_url": pdf_url,
                    "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""
                })
            
            return results
            
        except Exception as e:
            print(f"arXiv 搜索失败: {e}")
            return []
    
    def search_by_author(self, author_name: str, max_results: int = 10) -> List[Dict]:
        """
        按作者搜索论文
        
        Args:
            author_name: 作者姓名
            max_results: 最大结果数
        
        Returns:
            论文列表
        """
        query = f"au:{quote(author_name)}"
        return self.search(query, max_results=max_results)
    
    def search_by_category(self, category: str, max_results: int = 10) -> List[Dict]:
        """
        按分类搜索论文
        
        Args:
            category: 分类代码（如 cs.AI, cs.CL, cs.LG）
            max_results: 最大结果数
        
        Returns:
            论文列表
        """
        query = f"cat:{category}"
        return self.search(query, max_results=max_results, sort_by="submittedDate")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--type", choices=["all", "author", "category"], default="all", help="搜索类型")
    parser.add_argument("--limit", type=int, default=10, help="结果数量")
    args = parser.parse_args()
    
    api = ArxivAPI()
    
    if args.type == "author":
        results = api.search_by_author(args.query, max_results=args.limit)
    elif args.type == "category":
        results = api.search_by_category(args.query, max_results=args.limit)
    else:
        results = api.search(args.query, max_results=args.limit)
    
    print(json.dumps(results, ensure_ascii=False, indent=2))
