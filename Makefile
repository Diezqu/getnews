.PHONY: daily mock preview install

# Full daily run (uses DeepSeek API → real summaries → git push)
daily:
	python daily.py

# Quick test run without LLM and without pushing
mock:
	python daily.py --mock --no-push

# Open today's output in browser (macOS)
preview:
	open docs/index.html

# Install Python dependencies
install:
	pip install -r requirements.txt
