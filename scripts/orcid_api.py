#!/usr/bin/env python3
"""
ORCID API 封装模块
公开数据 API，无需认证即可访问
https://info.orcid.org/documentation/api-tutorials/api-tutorial-searching-the-orcid-registry/
"""

import requests
import json
import time
from typing import List, Dict, Optional

ORCID_PUBLIC_BASE = "https://pub.orcid.org/v3.0"

class OrcidAPI:
    """ORCID API 封装（公开数据）"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "AI-Talent-Graph/1.0"
        })
        self.last_request_time = 0
        self.min_interval = 0.5  # 2 请求/秒
    
    def _rate_limit(self):
        """频率限制"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索学者
        
        Args:
            query: 搜索关键词（姓名/机构）
            limit: 返回结果数量
        
        Returns:
            学者列表
        """
        self._rate_limit()
        
        params = {
            "q": query,
            "rows": min(limit, 20)  # ORCID 限制
        }
        
        try:
            url = f"{ORCID_PUBLIC_BASE}/search"
            resp = self.session.get(url, params=params, timeout=30)
            
            if resp.status_code != 200:
                print(f"ORCID API error: {resp.status_code}")
                return []
            
            data = resp.json()
            results = []
            
            for item in data.get("result", []):
                orcid_id = item.get("orcid-identifier", {}).get("path", "")
                
                # 获取基本信息
                profile = self.get_record(orcid_id)
                
                if profile:
                    results.append(profile)
            
            return results
            
        except Exception as e:
            print(f"ORCID 搜索失败: {e}")
            return []
    
    def get_record(self, orcid_id: str) -> Optional[Dict]:
        """
        获取学者档案
        
        Args:
            orcid_id: ORCID ID (如 0000-0001-2345-6789)
        
        Returns:
            学者档案
        """
        self._rate_limit()
        
        try:
            url = f"{ORCID_PUBLIC_BASE}/{orcid_id}/record"
            resp = self.session.get(url, timeout=30)
            
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            
            # 提取基本信息
            person = data.get("person", {})
            name = person.get("name", {})
            given_names = name.get("given-names", {}).get("value", "")
            family_name = name.get("family-name", {}).get("value", "")
            full_name = f"{given_names} {family_name}".strip() or "Unknown"
            
            # 其他名称
            other_names = []
            for on in person.get("other-names", {}).get("other-name", []):
                val = on.get("content", "")
                if val:
                    other_names.append(val)
            
            # 简介
            biography = ""
            bio_elem = person.get("biography", {})
            if bio_elem:
                biography = bio_elem.get("content", "")
            
            # 研究机构
            employments = []
            activities = data.get("activities-summary", {})
            emp_group = activities.get("employments", {}).get("employment-summary", [])
            for emp in emp_group:
                org = emp.get("organization", {})
                emp_data = {
                    "organization": org.get("name", ""),
                    "country": org.get("address", {}).get("country", ""),
                    "role": emp.get("role-title", ""),
                    "start_date": self._format_date(emp.get("start-date")),
                    "end_date": self._format_date(emp.get("end-date"))
                }
                employments.append(emp_data)
            
            # 教育背景
            educations = []
            edu_group = activities.get("educations", {}).get("education-summary", [])
            for edu in edu_group:
                org = edu.get("organization", {})
                edu_data = {
                    "institution": org.get("name", ""),
                    "country": org.get("address", {}).get("country", ""),
                    "degree": edu.get("role-title", ""),
                    "start_date": self._format_date(edu.get("start-date")),
                    "end_date": self._format_date(edu.get("end-date"))
                }
                educations.append(edu_data)
            
            # 论文数量估算
            works_count = len(activities.get("works", {}).get("group", []))
            
            return {
                "orcid_id": orcid_id,
                "name": full_name,
                "other_names": other_names,
                "biography": biography[:200] if len(biography) > 200 else biography,
                "employments": employments[:3],  # 最近3个
                "educations": educations[:3],
                "works_count": works_count,
                "profile_url": f"https://orcid.org/{orcid_id}"
            }
            
        except Exception as e:
            print(f"获取 ORCID 档案失败: {e}")
            return None
    
    def _format_date(self, date_obj) -> Optional[str]:
        """格式化日期"""
        if not date_obj:
            return None
        year = date_obj.get("year", {}).get("value", "")
        month = date_obj.get("month", {}).get("value", "")
        if year and month:
            return f"{year}-{month}"
        return year or None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--limit", type=int, default=10, help="结果数量")
    args = parser.parse_args()
    
    api = OrcidAPI()
    results = api.search(args.query, limit=args.limit)
    
    print(json.dumps(results, ensure_ascii=False, indent=2))
