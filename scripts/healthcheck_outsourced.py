#!/usr/bin/env python3
"""灵族外包项目健康检查 — 由灵通编排，定期巡检6个项目"""

import json
import sys
import time
import urllib.request
from dataclasses import dataclass, field


@dataclass
class Project:
    name: str
    port: int
    health_path: str = "/health"
    expected_in_service: bool = True

PROJECTS = [
    Project("灵律", 8002, "/api/health"),
    Project("灵声", 8100, "/health"),
    Project("灵康", 8200, "/health"),
    Project("灵依", 8900, "/api/health"),
]

TIMEOUT = 5


def check(project: Project) -> dict:
    url = f"http://127.0.0.1:{project.port}{project.health_path}"
    result = {
        "name": project.name,
        "port": project.port,
        "url": url,
        "status": "unknown",
        "response_time_ms": 0,
        "error": "",
    }
    t0 = time.time()
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        result["status"] = "ok" if resp.status == 200 else f"http_{resp.status}"
        result["response_time_ms"] = round((time.time() - t0) * 1000, 1)
    except urllib.request.HTTPError as e:
        result["status"] = f"http_{e.code}"
        result["response_time_ms"] = round((time.time() - t0) * 1000, 1)
    except Exception as e:
        result["status"] = "down"
        result["error"] = str(e)[:100]
        result["response_time_ms"] = round((time.time() - t0) * 1000, 1)
    return result


def main():
    results = []
    for p in PROJECTS:
        results.append(check(p))

    for r in results:
        icon = "🟢" if r["status"] == "ok" else "🔴"
        print(f"{icon} {r['name']} ({r['port']}): {r['status']} ({r['response_time_ms']}ms)")

    down = [r for r in results if r["status"] != "ok"]
    if down:
        print(f"\n⚠ {len(down)} project(s) need attention:")
        for r in down:
            print(f"  - {r['name']}: {r['status']} {r['error']}")

    json.dump(results, open("/tmp/outsourced_health.json", "w"), indent=2, ensure_ascii=False)
    return len(down)


if __name__ == "__main__":
    sys.exit(main())
