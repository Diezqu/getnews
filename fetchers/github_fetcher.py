"""Fetch trending AI repos from GitHub Search API (PAT optional but recommended)."""
import hashlib
import os
from datetime import date, timedelta

import requests

from fetchers.base import BaseFetcher, REGISTRY
from pipeline.config import get_config
from pipeline.schema import Item

_BASE = "https://api.github.com/search/repositories"
_LANG_MAP = {
    "Python": "Python", "TypeScript": "TS", "JavaScript": "JS",
    "Go": "Go", "Rust": "Rust", "Jupyter Notebook": "Jupyter",
}


class GitHubFetcher(BaseFetcher):
    source_id = "github"
    category = "learning"

    def fetch(self, target_date: date) -> list[Item]:
        cfg = get_config()["sources"]["github"]
        queries = cfg.get("queries", ["agent LLM"])
        max_per_query = cfg.get("max_per_query", 8)
        days_back = cfg.get("days_back", 30)
        since = (target_date - timedelta(days=days_back)).isoformat()

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        seen: set[str] = set()
        items: list[Item] = []
        for q in queries:
            params = {
                "q": f"{q} created:>{since}",
                "sort": "stars",
                "order": "desc",
                "per_page": max_per_query,
            }
            try:
                resp = requests.get(_BASE, params=params, headers=headers, timeout=15)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"  [warn] GitHub fetch failed for query '{q}': {e}")
                continue
            for repo in resp.json().get("items", []):
                full_name = repo.get("full_name", "")
                if full_name in seen:
                    continue
                seen.add(full_name)
                url = repo.get("html_url", "")
                desc = (repo.get("description") or "").strip()
                stars = int(repo.get("stargazers_count") or 0)
                lang = repo.get("language") or ""
                topics = repo.get("topics") or []
                pushed_at = repo.get("pushed_at") or ""
                tags = [_LANG_MAP.get(lang, lang)] if lang else []
                tags += [t for t in topics[:4] if t not in tags]
                item_id = hashlib.sha1(url.encode()).hexdigest()[:12]
                items.append(Item(
                    id=item_id,
                    source="github",
                    category="learning",
                    title=full_name,
                    url=url,
                    raw_content=desc,
                    stars=stars,
                    tags=tags[:5],
                    published_at=pushed_at,
                ))
        items.sort(key=lambda x: -x.stars)
        return items


REGISTRY.register(GitHubFetcher())
