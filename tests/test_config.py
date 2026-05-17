"""Config loader reads YAML and exposes typed dict access."""
from pathlib import Path

import pytest
import yaml

from pipeline.config import load_config, get_config


def test_load_config_returns_dict(repo_root: Path):
    cfg = load_config(repo_root / "config.yaml")
    assert isinstance(cfg, dict)
    assert "scoring" in cfg and "sources" in cfg and "llm" in cfg


def test_scoring_has_both_categories(repo_root):
    cfg = load_config(repo_root / "config.yaml")
    assert "learning" in cfg["scoring"]
    assert "job" in cfg["scoring"]


def test_sources_have_required_keys(repo_root):
    cfg = load_config(repo_root / "config.yaml")
    for src_name in ["arxiv", "hf_papers", "github", "hackernews",
                     "nowcoder", "china_ai", "coding_tool"]:
        assert src_name in cfg["sources"], f"missing source: {src_name}"
        assert "enabled" in cfg["sources"][src_name]


def test_get_config_caches(repo_root, monkeypatch):
    monkeypatch.chdir(repo_root)
    cfg1 = get_config()
    cfg2 = get_config()
    assert cfg1 is cfg2  # same object → cached


def test_llm_section_has_provider_and_model(repo_root):
    cfg = load_config(repo_root / "config.yaml")
    assert cfg["llm"]["provider"] in {"deepseek", "mock"}
    assert cfg["llm"]["model"]
