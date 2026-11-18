# 01 - MCP tool snapshot
# Mengambil definisi tool (tools/list) dari server MCP resmi, lalu membekukannya ke JSON.
# Semua file hasil ada di /kaggle/working dan diunduh untuk bahan terjemahan & eksperimen.

import asyncio
import csv
import datetime
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request

OUT = "/kaggle/working"
TMP = "/kaggle/tmp"
os.makedirs(TMP, exist_ok=True)

PY_SERVERS = ["mcp-server-git", "mcp-server-fetch", "mcp-server-time"]
NPM_SERVERS = ["@modelcontextprotocol/server-filesystem", "@modelcontextprotocol/server-memory"]
NODE_MAJOR = "v24"  # server Node resmi mensyaratkan node >= 24


def run(cmd, **kw):
    print("$", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)


# ---------- 1. Install ----------
run([sys.executable, "-m", "pip", "install", "-q", "mcp", *PY_SERVERS])

with urllib.request.urlopen("https://nodejs.org/dist/index.json") as r:
    node_version = next(v["version"] for v in json.load(r) if v["version"].startswith(NODE_MAJOR + "."))
tar_path = f"{TMP}/node.tar.xz"
urllib.request.urlretrieve(f"https://nodejs.org/dist/{node_version}/node-{node_version}-linux-x64.tar.xz", tar_path)
with tarfile.open(tar_path) as t:
    t.extractall(TMP)
os.environ["PATH"] = f"{TMP}/node-{node_version}-linux-x64/bin:" + os.environ["PATH"]
NPX = shutil.which("npx")
print("npx:", NPX, run(["node", "--version"]).stdout.strip())


def pip_version(pkg):
    for line in run([sys.executable, "-m", "pip", "show", pkg]).stdout.splitlines():
        if line.startswith("Version:"):
            return line.split(":", 1)[1].strip()


def npm_version(pkg):
    return run(["npm", "view", pkg, "version"]).stdout.strip()


versions = {p: pip_version(p) for p in ["mcp", *PY_SERVERS]}
versions.update({p: npm_version(p) for p in NPM_SERVERS})
print(json.dumps(versions, indent=2))

# ---------- 2. Sandbox untuk server yang butuh direktori ----------
fs_dir = f"{TMP}/sandbox_fs"
repo_dir = f"{TMP}/sandbox_repo"
os.makedirs(fs_dir, exist_ok=True)
os.makedirs(repo_dir, exist_ok=True)
if not os.path.exists(f"{repo_dir}/.git"):
    run(["git", "init", "-q", repo_dir])

# ---------- 3. Konfigurasi server ----------
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

SERVERS = {
    "filesystem": (
        "@modelcontextprotocol/server-filesystem",
        StdioServerParameters(
            command=NPX,
            args=["-y", f"@modelcontextprotocol/server-filesystem@{versions['@modelcontextprotocol/server-filesystem']}", fs_dir],
            env=dict(os.environ),
        ),
    ),
    "memory": (
        "@modelcontextprotocol/server-memory",
        StdioServerParameters(
            command=NPX,
            args=["-y", f"@modelcontextprotocol/server-memory@{versions['@modelcontextprotocol/server-memory']}"],
            env={**os.environ, "MEMORY_FILE_PATH": f"{TMP}/memory.jsonl"},
        ),
    ),
    "git": (
        "mcp-server-git",
        StdioServerParameters(command=sys.executable, args=["-m", "mcp_server_git", "--repository", repo_dir]),
    ),
    "fetch": (
        "mcp-server-fetch",
        StdioServerParameters(command=sys.executable, args=["-m", "mcp_server_fetch"]),
    ),
    "time": (
        "mcp-server-time",
        StdioServerParameters(command=sys.executable, args=["-m", "mcp_server_time", "--local-timezone", "Asia/Jakarta"]),
    ),
}


async def snapshot(params):
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            result = await session.list_tools()
            return init, result


async def main():
    servers, errors = [], {}
    for key, (package, params) in SERVERS.items():
        try:
            init, result = await asyncio.wait_for(snapshot(params), timeout=180)
            # by_alias=True -> nama field sesuai protokol MCP (inputSchema, serverInfo, ...)
            tools = [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in result.tools]
            init_info = init.model_dump(mode="json", by_alias=True, exclude_none=True)
            servers.append({
                "server": key,
                "package": package,
                "package_version": versions[package],
                "server_info": init_info.get("serverInfo", init_info.get("server_info")),
                "protocol_version": init_info.get("protocolVersion", init_info.get("protocol_version")),
                "tools": tools,
            })
            print(f"[OK] {key}: {len(tools)} tools", flush=True)
        except Exception as e:  # dicatat di manifest, tidak disembunyikan
            errors[key] = f"{type(e).__name__}: {e}"
            print(f"[FAIL] {key}: {errors[key]}", flush=True)
    return servers, errors


servers, errors = asyncio.run(main())

# ---------- 4. Simpan ----------
tools_path = f"{OUT}/tools_en.json"
with open(tools_path, "w", encoding="utf-8") as f:
    json.dump({"servers": servers}, f, ensure_ascii=False, indent=2)

with open(f"{OUT}/tools_en_flat.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["server", "tool_name", "field", "param_name", "text_en"])
    for s in servers:
        for t in s["tools"]:
            w.writerow([s["server"], t["name"], "tool_description", "", t.get("description", "")])
            schema = t.get("inputSchema", t.get("input_schema", {}))
            for pname, pschema in schema.get("properties", {}).items():
                w.writerow([s["server"], t["name"], "param_description", pname, pschema.get("description", "")])

names = [t["name"] for s in servers for t in s["tools"]]
duplicates = sorted({n for n in names if names.count(n) > 1})

with open(tools_path, "rb") as f:
    sha = hashlib.sha256(f.read()).hexdigest()

manifest = {
    "notebook": "01_tool_snapshot",
    "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "python": sys.version,
    "platform": platform.platform(),
    "node": run(["node", "--version"]).stdout.strip(),
    "package_versions": versions,
    "tool_counts": {s["server"]: len(s["tools"]) for s in servers},
    "total_tools": len(names),
    "duplicate_tool_names": duplicates,
    "errors": errors,
    "schema_key_check": sorted({k for s in servers for t in s["tools"] for k in t}),
    "tools_en_sha256": sha,
}
with open(f"{OUT}/snapshot_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(json.dumps(manifest, indent=2))
if errors:
    sys.exit(f"Server gagal: {list(errors)}")
