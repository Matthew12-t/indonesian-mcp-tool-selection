# 02 - Eksperimen pemilihan tool MCP: bahasa deskripsi (EN/ID) x bahasa kueri (EN/ID/campuran)
# Satu kernel Kaggle per model (konstanta MODEL).
# Tool TIDAK dijalankan: yang direkam hanya tool call pertama dari model.

import glob
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

OUT = "/kaggle/working"
MODEL = "qwen3:8b"  # satu kernel per model; baris ini diganti per kernel

DESC_LANGS = ["en", "id"]
QUERY_LANGS = ["en", "id", "mix"]
REPEATS = 3
TEMPERATURE = 0.0
SEED = 42
NUM_CTX = 16384
OLLAMA = "http://127.0.0.1:11434"

SYSTEM_PROMPT = (
    "You are an assistant that can use tools. The user's workspace directory is /workspace and the git repository "
    "is located at /workspace/app. The local timezone is Asia/Jakarta. Respond to the user's request by calling the "
    "single most appropriate tool."
)


def log(*a):
    print(datetime.now(timezone.utc).strftime("%H:%M:%S"), *a, flush=True)


def find_input(name):
    hits = glob.glob(f"/kaggle/input/**/{name}", recursive=True)
    if not hits:
        sys.exit(f"File input tidak ditemukan: {name}")
    return hits[0]


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def api(path, payload=None, timeout=600):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(OLLAMA + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


# ---------- 0. Validasi input ----------
log("Model:", MODEL)

paths = {n: find_input(n) for n in ["tools_en.json", "tools_id.json", "queries.json", "dataset_manifest.json"]}
manifest_in = json.load(open(paths["dataset_manifest.json"], encoding="utf-8"))
for n in ["tools_id.json", "queries.json"]:
    if sha256(paths[n]) != manifest_in["sha256"][n]:
        sys.exit(f"Hash {n} tidak cocok dengan dataset_manifest.json")
tools_src = {lang: json.load(open(paths[f"tools_{lang}.json"], encoding="utf-8")) for lang in DESC_LANGS}
queries = json.load(open(paths["queries.json"], encoding="utf-8"))["queries"]
log(f"{len(queries)} kueri dimuat; hash dataset cocok")


# ---------- 1. Tool -> format function calling ----------
def strip_titles(schema):
    """Hapus 'title' (label buatan generator skema) supaya satu-satunya teks yang berbeda antarbahasa adalah description."""
    if isinstance(schema, dict):
        out = {}
        for k, v in schema.items():
            if k == "title" and isinstance(v, str):
                continue
            if k == "properties" and isinstance(v, dict):
                out[k] = {pk: strip_titles(pv) for pk, pv in v.items()}
            else:
                out[k] = strip_titles(v)
        return out
    if isinstance(schema, list):
        return [strip_titles(x) for x in schema]
    return schema


def to_functions(snapshot):
    fns = []
    for s in snapshot["servers"]:
        for t in s["tools"]:
            fns.append({"type": "function", "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": strip_titles(t.get("inputSchema", {"type": "object", "properties": {}})),
            }})
    return fns


TOOLS = {lang: to_functions(tools_src[lang]) for lang in DESC_LANGS}
names_en = [f["function"]["name"] for f in TOOLS["en"]]
assert names_en == [f["function"]["name"] for f in TOOLS["id"]], "Urutan/nama tool EN dan ID berbeda"
TOOL_NAMES = set(names_en)
log(f"{len(names_en)} tool, urutan sama di kedua bahasa")

# ---------- 2. Install & jalankan Ollama ----------
if not shutil.which("ollama"):
    if not shutil.which("zstd"):
        subprocess.run(["apt-get", "update", "-qq"], check=True)
        subprocess.run(["apt-get", "install", "-y", "zstd"], check=True)
    subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
env = {**os.environ, "OLLAMA_HOST": "127.0.0.1:11434", "OLLAMA_KEEP_ALIVE": "24h", "OLLAMA_NUM_PARALLEL": "1"}
server = subprocess.Popen(["ollama", "serve"], env=env, stdout=open(f"{OUT}/ollama_server.log", "w"),
                          stderr=subprocess.STDOUT)
for _ in range(60):
    try:
        ollama_version = api("/api/version")["version"]
        break
    except Exception:
        time.sleep(2)
else:
    sys.exit("Ollama tidak mau menyala")
log("Ollama", ollama_version)

subprocess.run(["ollama", "pull", MODEL], check=True, env=env)
show = api("/api/show", {"model": MODEL})
capabilities = show.get("capabilities", [])
if "tools" not in capabilities:
    sys.exit(f"{MODEL} tidak mendukung tool calling di Ollama (capabilities={capabilities})")
model_digest = next((m["digest"] for m in api("/api/tags")["models"] if m["name"] == MODEL), None)
log("Capabilities:", capabilities, "| digest:", model_digest)

gpu = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                     capture_output=True, text=True).stdout.strip()
log("GPU:", gpu)


# ---------- 3. Panggil model ----------
def call(desc_lang, query_text):
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": query_text}],
        "tools": TOOLS[desc_lang],
        "stream": False,
        "options": {"temperature": TEMPERATURE, "seed": SEED, "num_ctx": NUM_CTX},
    }
    if "thinking" in capabilities:
        payload["think"] = False  # mode thinking dimatikan untuk semua model yang mendukungnya
    t0 = time.time()
    try:
        r = api("/api/chat", payload)
        err = None
    except Exception as e:
        r, err = {}, f"{type(e).__name__}: {e}"
    wall = time.time() - t0
    msg = r.get("message", {})
    calls = []
    for c in msg.get("tool_calls") or []:
        fn = c.get("function", {})
        args = fn.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                pass
        calls.append({"name": fn.get("name"), "arguments": args})
    return {
        "tool_calls": calls,
        "content": msg.get("content", ""),
        "prompt_tokens": r.get("prompt_eval_count"),
        "output_tokens": r.get("eval_count"),
        "total_duration_s": (r.get("total_duration") or 0) / 1e9,
        "wall_s": round(wall, 3),
        "error": err,
    }


# Ukur panjang prompt sekali per bahasa deskripsi untuk memastikan tidak terpotong oleh num_ctx.
prompt_check = {}
for dl in DESC_LANGS:
    probe = call(dl, queries[0]["query_en"])
    prompt_check[dl] = probe["prompt_tokens"]
    log(f"Token prompt (deskripsi {dl}):", probe["prompt_tokens"])
    if not probe["prompt_tokens"] or probe["prompt_tokens"] >= NUM_CTX - 512:
        sys.exit(f"Prompt terlalu panjang/terpotong untuk num_ctx={NUM_CTX}: {probe['prompt_tokens']}")

# ---------- 4. Loop eksperimen ----------
safe = MODEL.replace(":", "_").replace("/", "_")
raw_path = f"{OUT}/raw_results_{safe}.jsonl"
started = datetime.now(timezone.utc).isoformat()
n_done, total = 0, REPEATS * len(DESC_LANGS) * len(QUERY_LANGS) * len(queries)
with open(raw_path, "w", encoding="utf-8") as f:
    for rep in range(1, REPEATS + 1):
        for dl in DESC_LANGS:  # urutan kondisi sama untuk semua model
            for ql in QUERY_LANGS:
                for q in queries:
                    res = call(dl, q[f"query_{ql}"])
                    rec = {"model": MODEL, "rep": rep, "desc_lang": dl, "query_lang": ql, "qid": q["id"],
                           "category": q["category"], "gold_tool": q["gold_tool"], **res,
                           "first_tool": res["tool_calls"][0]["name"] if res["tool_calls"] else None,
                           "first_args": res["tool_calls"][0]["arguments"] if res["tool_calls"] else None,
                           "n_tool_calls": len(res["tool_calls"])}
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n_done += 1
                    if n_done % 150 == 0:
                        f.flush()
                        log(f"{n_done}/{total} (rep {rep}, desc {dl}, query {ql})")

run_manifest = {
    "notebook": "02_experiment",
    "model": MODEL,
    "model_digest": model_digest,
    "model_capabilities": capabilities,
    "ollama_version": ollama_version,
    "gpu": gpu,
    "python": sys.version,
    "platform": platform.platform(),
    "started_utc": started,
    "finished_utc": datetime.now(timezone.utc).isoformat(),
    "settings": {"temperature": TEMPERATURE, "seed": SEED, "num_ctx": NUM_CTX, "repeats": REPEATS,
                 "think": False if "thinking" in capabilities else None, "system_prompt": SYSTEM_PROMPT,
                 "desc_langs": DESC_LANGS, "query_langs": QUERY_LANGS},
    "prompt_tokens_probe": prompt_check,
    "n_queries": len(queries),
    "n_tools": len(names_en),
    "n_calls": n_done,
    "dataset_sha256": manifest_in["sha256"],
    "tools_en_sha256": sha256(paths["tools_en.json"]),
    "raw_results_sha256": sha256(raw_path),
}
with open(f"{OUT}/run_manifest_{safe}.json", "w", encoding="utf-8") as f:
    json.dump(run_manifest, f, ensure_ascii=False, indent=2)
log("Selesai:", json.dumps(run_manifest, indent=2))
server.terminate()
