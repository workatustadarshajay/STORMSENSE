"""Assembles the architecture website as its own publishable repository (its own GitHub Pages site).

    python infra/build_architecture_site.py ../STORMSENSE-architecture

The published copy differs from docs/architecture only where links would break outside this repository
(the documentation links) and the regenerate hint in the footer.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "architecture"
PAGES = ["system", "daily-pipeline", "approve-transfer", "transfer-lifecycle", "deploy"]

WORKFLOW = """name: Deploy architecture site to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
      - name: Configure GitHub Pages
        uses: actions/configure-pages@v5
      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: site
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
"""

README = """# StormSense architecture

Interactive architecture diagrams for StormSense, a weather-aware inventory transfer planner:
the system, the daily forecast pipeline, approving a transfer, the transfer lifecycle and how it is deployed.

The site is static HTML in [`site/`](site) and is published with GitHub Pages by
[`.github/workflows/pages.yml`](.github/workflows/pages.yml) on every push to `main`.

**One-time setup:** in the repository, open **Settings, Pages** and set **Source** to **GitHub Actions**.
After the first run the site is at `https://<owner>.github.io/<repository>/`.

Preview locally: `python3 -m http.server --directory site 8080`, then open http://localhost:8080.

The diagrams are generated from JSON in the main StormSense project with Archify; this repository holds the published output.
"""


def main(target: Path) -> None:
    site = target / "site"
    if site.exists():
        shutil.rmtree(site)
    (site / "assets").mkdir(parents=True)
    shutil.copy(SRC / "assets" / "manrope.woff2", site / "assets" / "manrope.woff2")
    for name in PAGES:
        shutil.copy(SRC / f"{name}.html", site / f"{name}.html")

    html = (SRC / "index.html").read_text()
    html, n = re.subn(r'\s*<nav class="links" aria-label="Documentation">.*?</nav>', "", html, flags=re.S)
    assert n == 1, "documentation links not found"
    footer = "<footer>Diagrams generated with Archify from StormSense&rsquo;s architecture sources.</footer>"
    html, n = re.subn(r"<footer>.*?</footer>", footer, html, flags=re.S)
    assert n == 1, "footer not found"
    (site / "index.html").write_text(html)

    (site / ".nojekyll").write_text("")
    wf = target / ".github" / "workflows"
    wf.mkdir(parents=True, exist_ok=True)
    (wf / "pages.yml").write_text(WORKFLOW)
    (target / "README.md").write_text(README)
    (target / ".gitignore").write_text(".DS_Store\n")
    print(f"built {target} ({sum(f.stat().st_size for f in site.rglob('*') if f.is_file()) // 1024} KB of site files)")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
