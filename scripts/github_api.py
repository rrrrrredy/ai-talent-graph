#!/usr/bin/env python3
"""
AI人才图谱 v2 - GitHub API 封装（内置版，无外部依赖）
"""
import requests
import os
import sys
from typing import List, Dict, Optional

BASE_URL = "https://api.github.com"

class GitHubAPI:
    def __init__(self, token: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Talent-Graph/2.0"
        })
        self.token = token or os.getenv("GH_API_TOKEN")
        if self.token:
            self.session.headers["Authorization"] = f"token {self.token}"
        else:
            print("⚠️  未检测到 GH_API_TOKEN，GitHub API 每小时限 60 次请求。", file=sys.stderr)

    def search_users(self, query: str, limit: int = 5) -> List[Dict]:
        try:
            r = self.session.get(f"{BASE_URL}/search/users",
                                 params={"q": query, "sort": "followers", "order": "desc", "per_page": limit},
                                 timeout=30)
            r.raise_for_status()
            return r.json().get("items", [])
        except Exception as e:
            print(f"GitHub 用户搜索失败: {e}", file=sys.stderr)
            return []

    def get_user(self, username: str) -> Optional[Dict]:
        try:
            r = self.session.get(f"{BASE_URL}/users/{username}", timeout=30)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"获取 GitHub 用户信息失败: {e}", file=sys.stderr)
            return None

    def analyze_tech_stack(self, username: str) -> Dict:
        try:
            r = self.session.get(f"{BASE_URL}/users/{username}/repos",
                                 params={"sort": "updated", "per_page": 50}, timeout=30)
            r.raise_for_status()
            repos = r.json()
        except Exception as e:
            print(f"获取 GitHub 仓库失败: {e}", file=sys.stderr)
            return {"top_languages": [], "total_stars": 0, "total_repos": 0}

        lang_counts = {}
        total_stars = 0
        for repo in repos:
            if repo.get("fork"):
                continue
            lang = repo.get("language")
            if lang:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            total_stars += repo.get("stargazers_count", 0)

        top_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
        return {
            "top_languages": [l for l, _ in top_langs[:5]],
            "total_stars": total_stars,
            "total_repos": len(repos)
        }

    def guess_github_username(self, full_name: str) -> List[Dict]:
        """根据学者姓名猜测 GitHub 用户名（返回候选列表，标注置信度）"""
        # 生成候选：姓名小写无空格、姓名用连字符、仅姓氏
        parts = full_name.lower().split()
        candidates_queries = [
            full_name,                          # 全名搜索
            "".join(parts),                     # 小写无空格
            "-".join(parts),                    # 连字符
        ]
        results = []
        for q in candidates_queries[:2]:        # 只搜前两个，节省 API 配额
            users = self.search_users(q, limit=3)
            for u in users:
                results.append({
                    "username": u.get("login"),
                    "avatar_url": u.get("avatar_url"),
                    "html_url": u.get("html_url"),
                    "confidence": "待验证"
                })
        # 去重
        seen = set()
        unique = []
        for r in results:
            if r["username"] not in seen:
                seen.add(r["username"])
                unique.append(r)
        return unique[:3]
