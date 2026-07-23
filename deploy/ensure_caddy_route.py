#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import cast

BASE = "http://127.0.0.1:2019/config/apps/http/servers/srv0/routes"


def request(method: str, url: str, payload: object | None = None) -> object:
    data = None if payload is None else json.dumps(payload).encode()
    headers = {} if data is None else {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as response:
        body = response.read()
    return cast(object, json.loads(body)) if body else None


def continuity_route() -> dict[str, object]:
    return {
        "match": [{"path": ["/continuityos/*"]}],
        "handle": [
            {"handler": "rewrite", "strip_path_prefix": "/continuityos"},
            {
                "handler": "reverse_proxy",
                "upstreams": [{"dial": "127.0.0.1:8082"}],
            },
        ],
    }


def is_continuity(route: dict[str, object]) -> bool:
    return any(
        "/continuityos/*" in matcher.get("path", [])
        for matcher in route.get("match", [])
        if isinstance(matcher, dict)
    )


def main() -> int:
    routes = request("GET", BASE)
    if not isinstance(routes, list):
        raise RuntimeError("Caddy returned an invalid route list")
    host_route = next(
        (
            route
            for route in routes
            if any(
                "aiautomatedsystems.ca" in matcher.get("host", [])
                for matcher in route.get("match", [])
                if isinstance(matcher, dict)
            )
        ),
        None,
    )
    if not isinstance(host_route, dict):
        raise RuntimeError("aiautomatedsystems.ca host route not found")
    outer = host_route["handle"][0]["routes"]
    if not isinstance(outer, list):
        raise RuntimeError("host route has no nested routes")
    if "/continuityos/*" in json.dumps(host_route):
        print("continuityos route already present")
        return 0
    catchall = next(
        (route for route in outer if isinstance(route, dict) and not route.get("match")),
        None,
    )
    if not isinstance(catchall, dict):
        raise RuntimeError("host route catchall not found")
    nested = catchall["handle"][0]["routes"]
    if not isinstance(nested, list) or not nested:
        raise RuntimeError("host route catchall has no nested route")
    fallback = nested[0]
    catchall["handle"][0]["routes"][0] = {
        "handle": [
            {
                "handler": "subroute",
                "routes": [continuity_route(), fallback],
            }
        ]
    }
    route_path = (
        f"{BASE}/{routes.index(host_route)}/handle/0/routes/"
        f"{outer.index(catchall)}/handle/0/routes/0"
    )
    request("PUT", route_path, catchall["handle"][0]["routes"][0])
    print("continuityos route installed")
    return 0


try:
    raise SystemExit(main())
except (OSError, urllib.error.URLError, KeyError, IndexError, TypeError, RuntimeError) as exc:
    print(f"continuityos route repair failed: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc
