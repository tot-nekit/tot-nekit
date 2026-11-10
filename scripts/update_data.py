"""Fetch public profile data. Uses only the Python standard library."""
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(first:100, privacy:PUBLIC, ownerAffiliations:OWNER,
      orderBy:{field:UPDATED_AT,direction:DESC}) {
      nodes { name description url stargazerCount forkCount isPrivate
        primaryLanguage { name color }
      }
    }
  }
}"""


def main():
    config = json.loads((ROOT / "profile.json").read_text())
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Set GH_TOKEN or GITHUB_TOKEN before refreshing data.")
    body = json.dumps({"query": QUERY, "variables": {"login": config["username"]}})
    env = os.environ.copy()
    env['GH_TOKEN'] = token
    response = subprocess.run(['gh', 'api', 'graphql', '--input', '-'],
                              input=body, text=True, capture_output=True,
                              env=env, timeout=60)
    if response.returncode:
        raise SystemExit('GitHub API request failed; previous data preserved.')
    result = json.loads(response.stdout)
    if result.get("errors"):
        raise SystemExit("GitHub GraphQL request failed; previous data preserved.")
    user = result.get("data", {}).get("user")
    if not user:
        raise SystemExit("GitHub user missing; previous data preserved.")
    if any(repo.get("isPrivate") for repo in user["repositories"]["nodes"]):
        raise SystemExit("Refusing to write private repository metadata.")
    output = {"updated": datetime.now(timezone.utc).date().isoformat(), **user}
    path = ROOT / "data" / "github.json"
    path.parent.mkdir(exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)
    print("Updated public GitHub data.")


if __name__ == "__main__":
    main()
