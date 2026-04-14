#!/usr/bin/env python3
"""
AI人才图谱 v2 - 主入口
整合 OpenAlex + arXiv + Semantic Scholar + ORCID + GitHub

运行方式（必须 cd 到脚本目录）：
  cd <skill_dir>/scripts
  python3 talent_graph.py search "multimodal llm" --limit 10
"""

import sys
import os
import json
import argparse
from typing import List, Dict, Optional

# 修复：确保同级模块可被 import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openalex_api import OpenAlexAPI
from arxiv_api import ArxivAPI
from orcid_api import OrcidAPI
from github_api import GitHubAPI
from semantic_scholar import SemanticScholarAPI


class AITalentGraph:
    def __init__(self):
        self.openalex = OpenAlexAPI()
        self.arxiv = ArxivAPI()
        self.orcid = OrcidAPI()
        self.github = GitHubAPI()
        self.ss = SemanticScholarAPI()

    # ──────────────────────────────────────────
    # 1. 搜索学者
    # ──────────────────────────────────────────
    def search_scholars(self, query: str, h_min: int = None,
                        lang_filter: str = None, limit: int = 10) -> Dict:
        results = {
            "query": query,
            "h_min": h_min,
            "lang_filter": lang_filter,
            "scholars": [],
            "warnings": []
        }

        # OpenAlex（主力）
        print(f"[1/2] OpenAlex 搜索: {query}...", file=sys.stderr)
        try:
            oa = self.openalex.search_authors(query, limit=min(limit * 2, 25))
            if h_min:
                oa = [r for r in oa if (r.get("h_index") or 0) >= h_min]
            results["scholars"] = oa[:limit]
        except Exception as e:
            msg = f"OpenAlex 搜索失败: {e}"
            print(msg, file=sys.stderr)
            results["warnings"].append(msg)

        # ORCID（补充，最多 3 条）
        print(f"[2/2] ORCID 补充搜索...", file=sys.stderr)
        try:
            orcid_results = self.orcid.search(query, limit=3)
            # 简单去重（按姓名）
            existing_names = {s.get("name", "").lower() for s in results["scholars"]}
            for r in orcid_results:
                if r.get("name", "").lower() not in existing_names:
                    results["scholars"].append({
                        "name": r.get("name"),
                        "institutions": [e.get("organization") for e in r.get("employments", [])[:1]],
                        "h_index": 0,
                        "cited_by_count": 0,
                        "works_count": r.get("works_count", 0),
                        "topics": [],
                        "orcid_url": r.get("profile_url"),
                        "source": "orcid"
                    })
        except Exception as e:
            results["warnings"].append(f"ORCID 数据暂不可用: {e}")

        # --lang 筛选（通过 GitHub tech_stack）
        if lang_filter and results["scholars"]:
            print(f"  → 按语言筛选: {lang_filter}...", file=sys.stderr)
            filtered = []
            for scholar in results["scholars"]:
                name = scholar.get("name", "")
                candidates = self.github.guess_github_username(name)
                matched = False
                for c in candidates:
                    uname = c.get("username")
                    if uname:
                        tech = self.github.analyze_tech_stack(uname)
                        if lang_filter.lower() in [l.lower() for l in tech.get("top_languages", [])]:
                            scholar["github_candidates"] = candidates
                            scholar["tech_stack"] = tech
                            matched = True
                            break
                if matched:
                    filtered.append(scholar)
            if filtered:
                results["scholars"] = filtered
            else:
                results["warnings"].append(f"未找到使用 {lang_filter} 的匹配学者，已返回未筛选结果")

        results["total"] = len(results["scholars"])
        return results

    # ──────────────────────────────────────────
    # 2. 生成学者画像
    # ──────────────────────────────────────────
    def generate_profile(self, name: str, github_username: str = None) -> Dict:
        profile = {
            "name": name,
            "academic": {},
            "semantic_scholar": {},
            "orcid": {},
            "engineering": {},
            "github_candidates": [],
            "insights": {},
            "warnings": []
        }

        # OpenAlex
        try:
            oa_list = self.openalex.search_authors(name, limit=3)
            if oa_list:
                author_id = oa_list[0].get("id")
                if author_id:
                    detail = self.openalex.get_author(author_id)
                    works = self.openalex.get_author_works(author_id, limit=5)
                    if detail:
                        detail["top_works"] = works
                        profile["academic"] = detail
        except Exception as e:
            profile["warnings"].append(f"OpenAlex 失败: {e}")

        # Semantic Scholar（补充 h-index 交叉验证）
        try:
            ss_list = self.ss.search_authors(name, limit=3)
            if ss_list:
                a = ss_list[0]
                profile["semantic_scholar"] = {
                    "h_index": a.get("hIndex"),
                    "citation_count": a.get("citationCount"),
                    "paper_count": a.get("paperCount"),
                    "url": f"https://www.semanticscholar.org/author/{a.get('authorId', '')}"
                }
        except Exception as e:
            profile["warnings"].append(f"Semantic Scholar 失败: {e}")

        # ORCID
        try:
            orcid_list = self.orcid.search(name, limit=2)
            if orcid_list:
                profile["orcid"] = orcid_list[0]
        except Exception as e:
            profile["warnings"].append(f"ORCID 数据暂不可用: {e}")

        # GitHub（优先用传入 username，否则自动猜测）
        if github_username:
            self._enrich_github(profile, github_username, verified=True)
        else:
            candidates = self.github.guess_github_username(name)
            profile["github_candidates"] = candidates
            if candidates:
                # 取第一个候选尝试拉取
                self._enrich_github(profile, candidates[0]["username"], verified=False)

        profile["insights"] = self._generate_insights(profile)
        return profile

    def _enrich_github(self, profile: Dict, username: str, verified: bool):
        try:
            user = self.github.get_user(username)
            if user:
                tech = self.github.analyze_tech_stack(username)
                profile["engineering"] = {
                    "username": username,
                    "name": user.get("name"),
                    "bio": user.get("bio"),
                    "company": user.get("company"),
                    "followers": user.get("followers"),
                    "public_repos": user.get("public_repos"),
                    "tech_stack": tech,
                    "profile_url": user.get("html_url"),
                    "verified": verified
                }
        except Exception as e:
            profile["warnings"].append(f"GitHub 数据获取失败: {e}")

    # ──────────────────────────────────────────
    # 3. 机构分析
    # ──────────────────────────────────────────
    def search_institution(self, name: str, limit: int = 10) -> Dict:
        results = {
            "query": name,
            "institutions": [],
            "top_authors": [],
            "warnings": []
        }
        try:
            insts = self.openalex.search_institution(name)
            results["institutions"] = insts
            if insts:
                inst_id = insts[0].get("id")
                authors = self.openalex.get_institution_authors(inst_id, limit=limit)
                results["top_authors"] = authors
        except Exception as e:
            results["warnings"].append(f"机构搜索失败: {e}")
        return results

    # ──────────────────────────────────────────
    # 4. 追踪最新论文（arXiv）
    # ──────────────────────────────────────────
    def latest_papers(self, query: str, limit: int = 5) -> Dict:
        results = {"query": query, "papers": [], "warnings": []}
        print(f"arXiv 搜索最新论文（有 3 秒限速，请稍候）...", file=sys.stderr)
        try:
            papers = self.arxiv.search(query, max_results=limit, sort_by="submittedDate")
            results["papers"] = papers
        except Exception as e:
            results["warnings"].append(f"arXiv 搜索失败: {e}")
        return results

    # ──────────────────────────────────────────
    # Format output (list style, IM-friendly)
    # ──────────────────────────────────────────
    def fmt_search(self, results: Dict) -> str:
        lines = []
        q = results["query"]
        h_min = results.get("h_min")
        lang = results.get("lang_filter")
        total = results.get("total", 0)

        lines.append(f"🕸️ AI人才图谱 - 找到 {total} 位学者")
        filter_info = []
        if h_min:
            filter_info.append(f"h-index ≥ {h_min}")
        if lang:
            filter_info.append(f"语言: {lang}")
        lines.append(f"搜索词: {q}" + (f"  过滤: {', '.join(filter_info)}" if filter_info else ""))
        lines.append("")

        if not results.get("scholars"):
            lines.append("❌ 未找到相关学者。建议：用英文关键词重试（如 'transformer attention'）")
        else:
            for i, s in enumerate(results["scholars"][:10], 1):
                name = s.get("name", "Unknown")
                inst = (s.get("institutions") or ["N/A"])[0] or "N/A"
                h_idx = s.get("h_index") or 0
                cites = s.get("cited_by_count") or 0
                works = s.get("works_count") or 0
                topics = "、".join((s.get("topics") or [])[:2]) or "N/A"
                oa_url = s.get("openalex_url") or ""

                lines.append(f"{i}. {name}")
                lines.append(f"   机构: {inst} | h-index: {h_idx} | 引用: {cites} | 论文: {works}")
                lines.append(f"   领域: {topics}")
                if oa_url:
                    lines.append(f"   🔗 {oa_url}")
                lines.append("")

        for w in results.get("warnings", []):
            lines.append(f"⚠️ {w}")

        lines.append("💡 提示: 用 `查学者 姓名` 获取完整画像")
        return "\n".join(lines)

    def fmt_profile(self, profile: Dict) -> str:
        lines = []
        name = profile.get("name", "Unknown")
        ins = profile.get("insights", {})

        lines.append(f"🕸️ {name} 的学者画像")
        lines.append(f"类型: {ins.get('talent_type', '-')}  影响力: {ins.get('influence_level', '-')}")
        lines.append("")

        acad = profile.get("academic", {})
        ss = profile.get("semantic_scholar", {})
        if acad or ss:
            h = acad.get("h_index") or ss.get("h_index") or 0
            cites = acad.get("cited_by_count") or ss.get("citation_count") or 0
            works = acad.get("works_count") or ss.get("paper_count") or 0
            insts = acad.get("institutions") or []
            topics = acad.get("topics") or []
            lines.append("📚 学术影响力")
            lines.append(f"  h-index: {h}  总引用: {cites}  论文数: {works}")
            if insts:
                lines.append(f"  机构: {', '.join(insts[:2])}")
            if topics:
                lines.append(f"  研究领域: {', '.join(topics[:3])}")
            # 代表作
            works_list = acad.get("top_works", [])
            if works_list:
                lines.append("  代表作:")
                for i, w in enumerate(works_list[:3], 1):
                    t = (w.get("title") or "")[:50]
                    y = w.get("publication_year", "")
                    c = w.get("cited_by_count", 0)
                    lines.append(f"    {i}. {t} ({y}, {c}引用)")
            if ss.get("url"):
                lines.append(f"  🔗 Semantic Scholar: {ss['url']}")
            if acad.get("openalex_url"):
                lines.append(f"  🔗 OpenAlex: {acad['openalex_url']}")
            lines.append("")

        eng = profile.get("engineering", {})
        if eng:
            verified_tag = "" if eng.get("verified") else " (待验证)"
            lines.append(f"💻 工程能力{verified_tag}")
            lines.append(f"  GitHub: @{eng.get('username')}  Followers: {eng.get('followers', 0)}")
            lines.append(f"  公开仓库: {eng.get('public_repos', 0)}  ⭐总星数: {eng.get('tech_stack', {}).get('total_stars', 0)}")
            langs = eng.get("tech_stack", {}).get("top_languages", [])
            if langs:
                lines.append(f"  技术栈: {', '.join(langs[:5])}")
            lines.append(f"  🔗 {eng.get('profile_url', '')}")
            lines.append("")
        elif profile.get("github_candidates"):
            lines.append("💻 GitHub 候选（请用 --github 参数确认）")
            for c in profile["github_candidates"][:3]:
                lines.append(f"  - @{c['username']} ({c['confidence']})  {c['html_url']}")
            lines.append("")

        orcid = profile.get("orcid", {})
        if orcid.get("profile_url"):
            lines.append(f"🔗 ORCID: {orcid['profile_url']}")

        for w in profile.get("warnings", []):
            lines.append(f"⚠️ {w}")

        return "\n".join(lines)

    def fmt_institution(self, results: Dict) -> str:
        lines = []
        lines.append(f"🏢 机构分析: {results['query']}")
        lines.append("")

        insts = results.get("institutions", [])
        if not insts:
            lines.append("❌ 未找到该机构。建议用英文名（如 Tsinghua University / ByteDance）")
        else:
            inst = insts[0]
            lines.append(f"机构: {inst.get('name', 'N/A')}")
            lines.append(f"国家: {inst.get('country', 'N/A')}  论文数: {inst.get('works_count', 0)}  总引用: {inst.get('cited_by_count', 0)}")
            if inst.get("openalex_url"):
                lines.append(f"🔗 {inst['openalex_url']}")
            lines.append("")

        authors = results.get("top_authors", [])
        if authors:
            lines.append(f"核心学者 Top {len(authors)}")
            for i, a in enumerate(authors, 1):
                lines.append(f"  {i}. {a.get('name', 'Unknown')}  h-index: {a.get('h_index', 0)}  引用: {a.get('cited_by_count', 0)}")

        for w in results.get("warnings", []):
            lines.append(f"⚠️ {w}")
        return "\n".join(lines)

    def fmt_latest(self, results: Dict) -> str:
        lines = []
        lines.append(f"📄 最新 arXiv 论文: {results['query']}")
        lines.append("")

        papers = results.get("papers", [])
        if not papers:
            lines.append("❌ 未找到相关论文")
        else:
            for i, p in enumerate(papers, 1):
                title = p.get("title", "Unknown")[:60]
                authors = "、".join((p.get("authors") or [])[:3])
                updated = p.get("updated") or str(p.get("published_year", ""))
                cats = "、".join((p.get("categories") or [])[:2])
                arxiv_url = p.get("arxiv_url", "")
                lines.append(f"{i}. {title}")
                lines.append(f"   作者: {authors}")
                lines.append(f"   更新: {updated}  分类: {cats}")
                if arxiv_url:
                    lines.append(f"   🔗 {arxiv_url}")
                lines.append("")

        for w in results.get("warnings", []):
            lines.append(f"⚠️ {w}")
        return "\n".join(lines)

    # ──────────────────────────────────────────
    # 内部：生成综合洞察
    # ──────────────────────────────────────────
    def _generate_insights(self, profile: Dict) -> Dict:
        acad = profile.get("academic", {})
        ss = profile.get("semantic_scholar", {})
        h = acad.get("h_index") or ss.get("h_index") or 0
        cites = acad.get("cited_by_count") or ss.get("citation_count") or 0
        works = acad.get("works_count") or ss.get("paper_count") or 0
        has_github = bool(profile.get("engineering"))
        has_academic = h > 0 or works > 0

        if has_github and has_academic:
            talent_type = "学术工程全栈型"
        elif has_github:
            talent_type = "工程型"
        elif has_academic:
            talent_type = "学术型"
        else:
            talent_type = "未知"

        if h >= 40 or cites >= 5000:
            level = "顶级"
        elif h >= 20 or cites >= 1000:
            level = "高"
        elif h >= 10 or cites >= 200:
            level = "中"
        else:
            level = "初"

        return {"talent_type": talent_type, "influence_level": level,
                "h_index": h, "citations": cites, "works_count": works}


def main():
    parser = argparse.ArgumentParser(description="AI人才图谱 v2")
    parser.add_argument("action", choices=["search", "profile", "institution", "latest"])
    parser.add_argument("query", help="搜索关键词 / 学者姓名 / 机构名")
    parser.add_argument("--github", help="GitHub 用户名（profile 模式可选）")
    parser.add_argument("--hmin", type=int, help="最低 h-index 筛选")
    parser.add_argument("--lang", help="编程语言筛选（如 python/javascript）")
    parser.add_argument("--limit", type=int, default=10, help="结果数量（最大 20）")
    parser.add_argument("--json", action="store_true", help="输出原始 JSON")
    args = parser.parse_args()

    limit = min(args.limit, 20)
    graph = AITalentGraph()

    if args.action == "search":
        data = graph.search_scholars(args.query, h_min=args.hmin,
                                     lang_filter=args.lang, limit=limit)
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else graph.fmt_search(data))

    elif args.action == "profile":
        data = graph.generate_profile(args.query, github_username=args.github)
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else graph.fmt_profile(data))

    elif args.action == "institution":
        data = graph.search_institution(args.query, limit=limit)
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else graph.fmt_institution(data))

    elif args.action == "latest":
        data = graph.latest_papers(args.query, limit=limit)
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else graph.fmt_latest(data))


if __name__ == "__main__":
    main()
