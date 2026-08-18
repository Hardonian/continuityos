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
                "upstreams": [{"dial": "127.0.0.1:8092"}],
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
    # Caddy assigns group names dynamically. The host fallback is the first
    # match-less subroute; it is not stable across config mutations and cannot
    # safely be identified by a hard-coded group name.
    catchall = next(
        (
            route
            for route in outer
            if isinstance(route, dict)
            and "match" not in route
            and isinstance(route.get("handle"), list)
            and route.get("handle")
            and isinstance(route["handle"][0], dict)
            and route["handle"][0].get("handler") == "subroute"
        ),
        None,
    )
    if not isinstance(catchall, dict):
        raise RuntimeError("host route catchall not found (no match-less subroute)")
    # Catchall structure: {"group": "group9", "handle": [{"handler": "subroute", "routes": [...]}]}
    catchall_handle = catchall.get("handle", [])
    if not isinstance(catchall_handle, list) or not catchall_handle:
        raise RuntimeError("catchall has no handle")
    catchall_subroute = catchall_handle[0]
    if catchall_subroute.get("handler") != "subroute":
        raise RuntimeError("catchall handle is not a subroute")
    catchall_routes = catchall_subroute.get("routes", [])
    if not isinstance(catchall_routes, list) or not catchall_routes:
        raise RuntimeError("catchall subroute has no nested routes")
    existing_idx = next(
        (
            idx
            for idx, route in enumerate(catchall_routes)
            if isinstance(route, dict) and "/continuityos/*" in json.dumps(route)
        ),
        None,
    )
    if existing_idx is not None:
        existing = catchall_routes[existing_idx]
        existing_json = json.dumps(existing)
        if "127.0.0.1:8092" in existing_json:
            print("continuityos route already present")
            return 0
        updated_json = existing_json.replace("127.0.0.1:8082", "127.0.0.1:8092")
        route_path = (
            f"{BASE}/{routes.index(host_route)}/handle/0/routes/"
            f"{outer.index(catchall)}/handle/0/routes/{existing_idx}"
        )
        request("PUT", route_path, json.loads(updated_json))
        print("continuityos route upstream updated")
        return 0
    # Find the fallback (reverse_proxy)
    fallback_idx = None
    for idx, route in enumerate(catchall_routes):
        if isinstance(route, dict) and "handle" in route:
            handle = route["handle"]
            if isinstance(handle, list) and handle and handle[0].get("handler") == "reverse_proxy":
                    fallback_idx = idx
                    break
    if fallback_idx is None:
        raise RuntimeError("no reverse_proxy fallback found in catchall")
    fallback = catchall_routes[fallback_idx]
    # Replace the fallback with a subroute containing continuity_route + fallback
    catchall_routes[fallback_idx] = {
        "handle": [
            {
                "handler": "subroute",
                "routes": [continuity_route(), fallback],
            }
        ]
    }
    # Update the catchall in Caddy
    route_path = (
        f"{BASE}/{routes.index(host_route)}/handle/0/routes/"
        f"{outer.index(catchall)}/handle/0/routes/{fallback_idx}"
    )
    request("PUT", route_path, catchall_routes[fallback_idx])
    print("continuityos route installed")
    return 0


try:
    raise SystemExit(main())
except (OSError, urllib.error.URLError, KeyError, IndexError, TypeError, RuntimeError) as exc:
    print(f"continuityos route repair failed: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc
