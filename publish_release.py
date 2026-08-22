import configparser
import json
from pathlib import Path
import subprocess
import urllib.request

config = configparser.ConfigParser()
config.read(r"C:\Users\stavd\.github\config")
token = config.get("default", "token")
username = config.get("default", "username")
remote_url = f"https://{username}:{token}@github.com/sdoolman/blindly_follows.git"

# 1. Commit and push changes
subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-m", "docs: add fsm diagram, release workflows, gitlab ci and remove legacy pipfile"], check=True)
subprocess.run(["git", "push", remote_url, "development:development"], check=True)

# 2. Sync main branch with latest commit
subprocess.run(["git", "push", remote_url, "development:main", "--force"], check=True)

# 3. Tag and push v0.1.0 tag
subprocess.run(["git", "tag", "-fa", "v0.1.0", "-m", "v0.1.0: Modernized Blind State Machine Execution POC"], check=True)
subprocess.run(["git", "push", remote_url, "v0.1.0", "--force"], check=True)
print("Pushed development, main, and tag v0.1.0 successfully!")

# 4. Create GitHub Release v0.1.0
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

body_text = """Reference implementation for the research paper *"Blindly Follow: SITS CRT and FHE for DCLSMPC of DUFSM"* (CSCML 2021).

### Key Features & Updates:
- **PEP 621 Standard**: Modern `pyproject.toml` packaging.
- **Explicit Algebraic Ring Arithmetic**: Faithful implementation of square-and-multiply modular exponentiation, recursive Extended Euclidean GCD, and Lagrange basis polynomials over $\\mathbb{Z}_M$.
- **Complete Test Coverage**: 31 comprehensive unit tests (`pytest`).
- **Containerization**: Multi-stage `Dockerfile` and `docker-compose.yml`.
- **CI/CD Pipelines**: GitHub Actions workflows (`ci.yml`, `release.yml`) and GitLab CI pipeline (`.gitlab-ci.yml`).
- **State Machine Visualization**: Embedded native Mermaid FSM diagram and `diagram.png`.
"""

release_payload = {
    "tag_name": "v0.1.0",
    "target_commitish": "main",
    "name": "v0.1.0: Modernized Blind State Machine Execution POC",
    "body": body_text,
    "draft": False,
    "prerelease": False,
}

req = urllib.request.Request(
    "https://api.github.com/repos/sdoolman/blindly_follows/releases",
    headers=headers,
    method="POST",
    data=json.dumps(release_payload).encode("utf-8"),
)

try:
    with urllib.request.urlopen(req) as r:
        rel = json.loads(r.read())
        print(f"Created GitHub Release: {rel.get('html_url')}")
except Exception as e:
    print(f"Release response: {e}")
    if hasattr(e, "read"):
        print(e.read().decode())
