#!/usr/bin/env python3
"""Prometheus の値から静的なステータスページ(index.html)を作り直す。

標準ライブラリだけを使う。INTERVAL 秒ごとに作り直し、書き出しは一時ファイル経由で
行うため、配信側(nginx)は途中まで書かれたページを読まない。
取得に失敗した場合は、エラーを表示したページに置き換える。
負荷の推移(直近 1 時間)は取得できなくても、ページ全体は表示する。
"""
import datetime
import html
import json
import os
import sys
import time
import urllib.parse
import urllib.request

# 表示する時刻は JST 固定。コンテナにはタイムゾーンのデータが無いため、オフセットで直接指定する
JST = datetime.timezone(datetime.timedelta(hours=9), "JST")

PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://127.0.0.1:9090").rstrip("/")
INTERVAL = int(os.environ.get("INTERVAL", "60"))
CLUSTER_NAME = os.environ.get("CLUSTER_NAME", "JARVIS")
OUT_DIR = os.environ.get("OUT_DIR", "/site")
TIMEOUT = 10

# 表示するファイルシステム(tmpfs や overlay などは除外する)
FS_TYPES = "ext4|xfs|btrfs|zfs|vfat|nfs.*"
JOB = 'job="node_exporter"'
# NAS は snmp_exporter(job="nas")で取得し、ボリュームだけを表示する
NAS_JOB = 'job="nas"'
NAS_VOLUMES = 'mountpoint=~"/volume.*"'
HISTORY_MINUTES = 60


def query(promql):
    url = PROMETHEUS_URL + "/api/v1/query?" + urllib.parse.urlencode({"query": promql})
    with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
        body = json.load(resp)
    if body.get("status") != "success":
        raise RuntimeError("Prometheus クエリに失敗しました: " + promql)
    return body["data"]["result"]


def query_range(promql, minutes):
    end = time.time()
    params = {"query": promql, "start": end - minutes * 60, "end": end, "step": 60}
    url = PROMETHEUS_URL + "/api/v1/query_range?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
        body = json.load(resp)
    if body.get("status") != "success":
        raise RuntimeError("Prometheus 範囲クエリに失敗しました: " + promql)
    return body["data"]["result"]


def by_instance(promql):
    values = {}
    for item in query(promql):
        values[item["metric"].get("instance", "")] = float(item["value"][1])
    return values


def disks(size_promql, avail_promql):
    sizes = {}
    for item in query(size_promql):
        m = item["metric"]
        sizes[(m.get("instance", ""), m.get("mountpoint", ""))] = float(item["value"][1])
    result = {}
    for item in query(avail_promql):
        m = item["metric"]
        key = (m.get("instance", ""), m.get("mountpoint", ""))
        if key in sizes:
            result.setdefault(key[0], []).append((key[1], float(item["value"][1]), sizes[key]))
    return result


def load_history():
    # 直近 1 時間の負荷の推移。取得できなければ空にして、グラフだけ省く
    try:
        history = {}
        for item in query_range("node_load1{%s}" % JOB, HISTORY_MINUTES):
            history[item["metric"].get("instance", "")] = [float(v) for _, v in item["values"]]
        return history
    except Exception as exc:
        print("load history failed: %s" % exc, file=sys.stderr, flush=True)
        return {}


def nas_status():
    # snmp_exporter 経由の NAS(job="nas")。取得できなくても、クラスタのページは表示する
    try:
        up = by_instance("up{%s}" % NAS_JOB)
        totals, used, units = {}, {}, {}
        for store, metric in ((totals, "hrStorageSize"), (used, "hrStorageUsed"), (units, "hrStorageAllocationUnits")):
            for item in query("%s{%s,%s}" % (metric, NAS_JOB, NAS_VOLUMES)):
                m = item["metric"]
                store[(m.get("instance", ""), m.get("mountpoint", ""))] = float(item["value"][1])
        volumes = {}
        for key, blocks in totals.items():
            if key not in used or key not in units:
                continue
            size = blocks * units[key]
            usage = used[key] * units[key]
            volumes.setdefault(key[0], []).append((key[1], size - usage, size))
        return {"up": up, "volumes": volumes}
    except Exception as exc:
        print("nas status failed: %s" % exc, file=sys.stderr, flush=True)
        return {"up": {}, "volumes": {}}


def collect():
    data = {
        "nas": nas_status(),
        # 直近 30 日に一度でも報告したホスト(停止中のホストも一覧に残す)
        "seen": by_instance(
            "count by (instance) (last_over_time(node_uname_info{%s}[30d]))" % JOB
        ),
        "up": by_instance("up{%s}" % JOB),
        "load1": by_instance("node_load1{%s}" % JOB),
        "mem_total": by_instance("node_memory_MemTotal_bytes{%s}" % JOB),
        "mem_avail": by_instance("node_memory_MemAvailable_bytes{%s}" % JOB),
        "cores": by_instance("count by (instance) (node_cpu_seconds_total{%s,mode=\"idle\"})" % JOB),
        "boot": by_instance("node_boot_time_seconds{%s}" % JOB),
        "disks": disks(
            "node_filesystem_size_bytes{%s,fstype=~\"%s\"}" % (JOB, FS_TYPES),
            "node_filesystem_avail_bytes{%s,fstype=~\"%s\"}" % (JOB, FS_TYPES),
        ),
        "history": load_history(),
    }
    kernel = {}
    for item in query("node_uname_info{%s}" % JOB):
        m = item["metric"]
        kernel[m.get("instance", "")] = m.get("release", "")
    data["kernel"] = kernel
    return data


def fmt_gib(value):
    return "%.1f GiB" % (value / 1024 ** 3)


def fmt_uptime(seconds):
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    return "%d日 %d時間 %d分" % (days, hours, minutes)


def status_of(name, data):
    if name not in data["up"]:
        return "報告なし", "down"
    if data["up"][name] == 1:
        return "稼働中", "ok"
    return "停止", "down"


def meter(percent):
    pct = max(0.0, min(100.0, percent))
    level = "crit" if pct >= 90 else "warn" if pct >= 70 else "ok"
    return '<div class="meter"><div class="fill %s" style="width:%.0f%%"></div></div>' % (
        level,
        pct,
    )


def sparkline(values):
    if len(values) < 2:
        return ""
    width, height, pad = 160, 36, 2
    top = max(max(values), 1.0)
    step = width / (len(values) - 1)
    points = " ".join(
        "%.1f,%.1f" % (i * step, height - pad - (v / top) * (height - 2 * pad))
        for i, v in enumerate(values)
    )
    return (
        '<svg class="spark" viewBox="0 0 %d %d" role="img" aria-label="直近 1 時間の負荷">'
        '<polyline points="%s" fill="none" stroke="currentColor" stroke-width="2"/></svg>'
        % (width, height, points)
    )


def render_card(name, data):
    label, css = status_of(name, data)
    parts = [
        '<section class="card %s">' % css,
        '<header><h2>%s</h2><span class="badge %s">%s</span></header>'
        % (html.escape(name), css, label),
    ]
    meta = []
    if name in data["boot"]:
        meta.append("稼働 " + fmt_uptime(time.time() - data["boot"][name]))
    if name in data["kernel"]:
        meta.append(data["kernel"][name])
    if name in data["cores"]:
        meta.append("%d コア" % data["cores"][name])
    if meta:
        parts.append('<p class="meta">%s</p>' % html.escape(" / ".join(meta)))

    if name in data["load1"]:
        load = data["load1"][name]
        cores = data["cores"].get(name)
        bar = meter(load / cores * 100) if cores else ""
        parts.append(
            '<div class="row"><span>負荷 %.2f</span>%s</div>%s'
            % (load, sparkline(data["history"].get(name, [])), bar)
        )
    if name in data["mem_total"] and name in data["mem_avail"]:
        total = data["mem_total"][name]
        used_pct = (1 - data["mem_avail"][name] / total) * 100
        parts.append(
            '<div class="row"><span>メモリ %.0f%%</span><span class="muted">総量 %s</span></div>%s'
            % (used_pct, fmt_gib(total), meter(used_pct))
        )
    for mount, avail, size in sorted(data["disks"].get(name, [])):
        used_pct = (1 - avail / size) * 100 if size else 0
        parts.append(
            '<div class="row"><span>%s %.0f%%</span><span class="muted">残り %s / %s</span></div>%s'
            % (html.escape(mount), used_pct, fmt_gib(avail), fmt_gib(size), meter(used_pct))
        )
    parts.append("</section>")
    return "".join(parts)


SANS = '"Noto Sans JP", "Hiragino Sans", system-ui, sans-serif'
MONO = "Consolas, Menlo, monospace"
MARU = '"Zen Maru Gothic", "Hiragino Maru Gothic ProN", "Noto Sans JP", sans-serif'
ANGULAR = "polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 16px 100%, 0 calc(100% - 16px))"
# テーマ: (id, 表示名, 色・形・フォントの値)。値を CSS 変数にして切り替える
THEMES = [
    ("light", "白背景", {
        "bg": "#ffffff", "pattern": "none", "pattern-size": "auto",
        "card": "#ffffff", "text": "#111111", "muted": "#555555",
        "line": "#d4d4d8", "line-w": "1px", "track": "#e5e5e5",
        "ok": "#0f7a3a", "warn": "#b45309", "crit": "#c81e1e", "accent": "#2563eb",
        "badge-text": "#ffffff", "radius": "10px", "clip": "none", "shadow": "none",
        "card-top": "4px", "body-font": SANS, "head-font": SANS, "head-case": "none", "head-spacing": "0",
    }),
    ("dark", "黒背景", {
        "bg": "#0a0a0a", "pattern": "none", "pattern-size": "auto",
        "card": "#141414", "text": "#ececec", "muted": "#9a9a9a",
        "line": "#2e2e2e", "line-w": "1px", "track": "#2a2a2a",
        "ok": "#4ade80", "warn": "#fbbf24", "crit": "#f87171", "accent": "#a3a3a3",
        "badge-text": "#000000", "radius": "10px", "clip": "none", "shadow": "none",
        "card-top": "4px", "body-font": SANS, "head-font": SANS, "head-case": "none", "head-spacing": "0",
    }),
    ("eva", "某アニメ風", {
        # 参考デザインの値: 背景 #0b0e13、本文 #fff1dc、琥珀 #ffcf8a、橙 #ff9a3c、黄 #ffd23d、赤 #ff4d4d
        "bg": "#0b0e13",
        "pattern": "linear-gradient(rgba(255,207,138,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,207,138,0.05) 1px, transparent 1px)",
        "pattern-size": "32px 32px",
        "card": "rgba(20,24,32,0.55)", "text": "#fff1dc", "muted": "#8d96a5",
        "line": "rgba(255,207,138,0.75)", "line-w": "1px", "track": "#2b323e",
        "ok": "#ffd23d", "warn": "#ff9a3c", "crit": "#ff4d4d", "accent": "#ffcf8a",
        "badge-text": "#0b0e13", "radius": "8px", "clip": "none",
        "shadow": "0 0 0.6rem rgba(255,138,31,0.45)", "card-top": "3px",
        "body-font": '"LINE Seed JP", "Hiragino Sans", sans-serif',
        "head-font": '"Oswald", "Arial Narrow", sans-serif', "head-case": "uppercase", "head-spacing": "0.06em",
    }),
    ("terminal", "端末グリーン", {
        "bg": "#000000", "pattern": "repeating-linear-gradient(0deg, rgba(51,255,102,0.06) 0 1px, transparent 1px 3px)",
        "pattern-size": "auto",
        "card": "#010a03", "text": "#33ff66", "muted": "#1f9e44",
        "line": "#1f9e44", "line-w": "1px", "track": "#0d3b18",
        "ok": "#33ff66", "warn": "#ffd33d", "crit": "#ff4d4d", "accent": "#33ff66",
        "badge-text": "#000000", "radius": "0", "clip": "none", "shadow": "0 0 10px rgba(51,255,102,0.15)",
        "card-top": "3px", "body-font": MONO, "head-font": MONO, "head-case": "uppercase", "head-spacing": "0.06em",
    }),
    ("pop", "ポップ", {
        "bg": "#fff6fb", "pattern": "radial-gradient(#ffd6e7 2px, transparent 2px)", "pattern-size": "18px 18px",
        "card": "#ffffff", "text": "#2b2d42", "muted": "#5c5f7a",
        "line": "#2b2d42", "line-w": "3px", "track": "#e9ecf5",
        "ok": "#06a77d", "warn": "#ff9f1c", "crit": "#ef476f", "accent": "#ff8fab",
        "badge-text": "#ffffff", "radius": "18px", "clip": "none", "shadow": "4px 4px 0 #2b2d42",
        "card-top": "3px", "body-font": MARU, "head-font": MARU, "head-case": "none", "head-spacing": "0",
    }),
    ("cyber", "サイバー青", {
        "bg": "#04111f",
        "pattern": "linear-gradient(rgba(56,189,248,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(56,189,248,0.10) 1px, transparent 1px)",
        "pattern-size": "24px 24px",
        "card": "#081e36", "text": "#cfefff", "muted": "#6fa8c9",
        "line": "#0ea5e9", "line-w": "1px", "track": "#0b2a45",
        "ok": "#34d399", "warn": "#facc15", "crit": "#fb7185", "accent": "#38bdf8",
        "badge-text": "#001018", "radius": "2px", "clip": ANGULAR, "shadow": "0 0 14px rgba(56,189,248,0.2)",
        "card-top": "4px", "body-font": SANS, "head-font": MONO, "head-case": "uppercase", "head-spacing": "0.1em",
    }),
    ("nerv", "情報パネル", {
        "bg": "#101214", "pattern": "none", "pattern-size": "auto",
        "card": "#1a1d21", "text": "#e8eaed", "muted": "#9aa0a6",
        "line": "#3a4048", "line-w": "1px", "track": "#2b3036",
        "ok": "#22c55e", "warn": "#f5a524", "crit": "#ef4444", "accent": "#e4572e",
        "badge-text": "#111111", "radius": "4px", "clip": "none", "shadow": "none",
        "card-top": "4px", "body-font": SANS, "head-font": SANS, "head-case": "none", "head-spacing": "0.02em",
    }),
]
THEME_IDS = [tid for tid, _, _ in THEMES]


def theme_css():
    # 先頭の白背景は :root(テーマ未設定・スクリプト無効時)にも使う
    blocks = []
    for index, (tid, _, values) in enumerate(THEMES):
        decl = " ".join("--%s: %s;" % (key, val) for key, val in values.items())
        selector = ":root" if index == 0 else 'html[data-theme="%s"]' % tid
        blocks.append("%s { %s }" % (selector, decl))
    return "\n  ".join(blocks)


THEME_CSS = theme_css()
THEME_SELECT = '<select id="theme-select" aria-label="テーマ">%s</select>' % "".join(
    '<option value="%s">%s</option>' % (tid, html.escape(label)) for tid, label, _ in THEMES
)

# 保存済みのテーマを <head> で先に適用し、表示のちらつきを防ぐ。未設定や不正な値は OS の設定に従う
HEAD_SCRIPT = """(function () {
  var themes = %s;
  var theme = null;
  try { theme = localStorage.getItem("status-theme"); } catch (e) {}
  if (themes.indexOf(theme) < 0) {
    theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.setAttribute("data-theme", theme);
})();""" % json.dumps(THEME_IDS)

BODY_SCRIPT = """(function () {
  var root = document.documentElement;
  var select = document.getElementById("theme-select");
  select.value = root.getAttribute("data-theme");
  select.addEventListener("change", function () {
    root.setAttribute("data-theme", select.value);
    try { localStorage.setItem("status-theme", select.value); } catch (e) {}
  });
  // 現在時刻は閲覧者のブラウザで毎秒更新する。表示は JST に固定する
  var clock = document.getElementById("clock-now");
  var formatter = new Intl.DateTimeFormat("ja-JP", {
    timeZone: "Asia/Tokyo", year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false
  });
  function tick() {
    clock.textContent = formatter.format(new Date()) + " JST";
  }
  tick();
  setInterval(tick, 1000);
})();"""

PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="{refresh}">
<title>{cluster} Cluster Status</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=LINE+Seed+JP:wght@400;700&family=Oswald:wght@500&display=swap">
<script>
{head_script}
</script>
<style>
  {theme_css}
  body {{
    font-family: var(--body-font); margin: 16px; color: var(--text);
    background-color: var(--bg); background-image: var(--pattern); background-size: var(--pattern-size);
  }}
  .head {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
    border-bottom: 3px solid var(--accent); padding-bottom: 8px; margin-bottom: 12px; }}
  h1 {{ font-family: var(--head-font); font-size: 20px; margin: 0; letter-spacing: var(--head-spacing);
    text-transform: var(--head-case); color: var(--accent); }}
  .clock-wrap {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
  .clock {{ font-family: var(--head-font); font-size: 18px; letter-spacing: var(--head-spacing); color: var(--text);
    font-variant-numeric: tabular-nums; }}
  #theme-select {{ font: inherit; font-size: 13px; padding: 6px 8px; border: 2px solid var(--accent);
    background: var(--card); color: var(--text); border-radius: var(--radius); }}
  h2 {{ font-family: var(--head-font); font-size: 16px; margin: 0; letter-spacing: var(--head-spacing);
    text-transform: var(--head-case); }}
  .note {{ color: var(--muted); font-size: 13px; margin: 0 0 16px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }}
  .card {{ background: var(--card); border: var(--line-w) solid var(--line); border-top: var(--card-top) solid var(--crit);
    border-radius: var(--radius); padding: 12px 14px; box-shadow: var(--shadow); clip-path: var(--clip); }}
  .card.ok {{ border-top-color: var(--ok); }}
  .card header {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; }}
  .badge {{ font-family: var(--head-font); font-size: 12px; font-weight: 700; padding: 2px 8px;
    border-radius: var(--radius); color: var(--badge-text); white-space: nowrap; letter-spacing: var(--head-spacing); }}
  .badge.ok {{ background: var(--ok); }}
  .badge.down {{ background: var(--crit); }}
  .meta {{ color: var(--muted); font-size: 12px; margin: 6px 0 0; }}
  .row {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 13px; margin-top: 10px; }}
  .muted {{ color: var(--muted); font-size: 12px; }}
  .meter {{ height: 8px; background: var(--track); overflow: hidden; margin-top: 4px; border-radius: var(--radius); }}
  .fill {{ height: 100%; }}
  .fill.ok {{ background: var(--ok); }}
  .fill.warn {{ background: var(--warn); }}
  .fill.crit {{ background: var(--crit); }}
  .spark {{ width: 160px; height: 36px; color: var(--ok); flex-shrink: 0; }}
  .section {{ font-family: var(--head-font); font-size: 16px; text-transform: var(--head-case);
    letter-spacing: var(--head-spacing); margin: 22px 0 8px; padding-left: 8px; border-left: 6px solid var(--accent); }}
  .error {{ border: 2px solid var(--crit); color: var(--crit); padding: 8px; background: var(--card);
    border-radius: var(--radius); }}
  /* 某アニメ風: 半透明のパネル、発光する題名、枠で囲んだ区切り見出し */
  html[data-theme="eva"] h1 {{ color: var(--text); text-shadow: 0 0 0.6rem rgba(255,138,31,0.85); }}
  html[data-theme="eva"] .card {{ backdrop-filter: blur(14px) saturate(1.4); }}
  html[data-theme="eva"] .card header h2 {{ color: var(--text); }}
  html[data-theme="eva"] .section {{ display: inline-block; color: var(--accent); border: 1px solid var(--accent);
    border-left-width: 1px; padding: 2px 10px; border-radius: 6px; }}
</style>
</head>
<body>
<div class="head">
<h1>{cluster} Cluster Status</h1>
<div class="clock-wrap"><span id="clock-now" class="clock">--/--/-- --:--:-- JST</span>{theme_select}</div>
</div>
<p class="note">最終更新: {updated}(約 {refresh} 秒ごとに更新) / {summary}</p>
{body}
<script>
{body_script}
</script>
</body>
</html>
"""


def render_nas_card(name, nas):
    value = nas["up"].get(name)
    if value is None:
        label, css = "報告なし", "down"
    elif value == 1:
        label, css = "稼働中", "ok"
    else:
        label, css = "停止", "down"
    parts = [
        '<section class="card %s">' % css,
        '<header><h2>%s</h2><span class="badge %s">%s</span></header>'
        % (html.escape(name), css, label),
    ]
    for mount, avail, size in sorted(nas["volumes"].get(name, [])):
        used_pct = (1 - avail / size) * 100 if size else 0
        parts.append(
            '<div class="row"><span>%s %.0f%%</span><span class="muted">残り %s / %s</span></div>%s'
            % (html.escape(mount), used_pct, fmt_gib(avail), fmt_gib(size), meter(used_pct))
        )
    parts.append("</section>")
    return "".join(parts)


def render(data):
    names = sorted(data["seen"].keys())
    up = sum(1 for name in names if status_of(name, data)[1] == "ok")
    cards = "".join(render_card(name, data) for name in names)
    body = '<div class="grid">%s</div>' % cards
    nas = data["nas"]
    nas_names = sorted(nas["up"].keys())
    if nas_names:
        nas_cards = "".join(render_nas_card(name, nas) for name in nas_names)
        body += '<h2 class="section">NAS</h2><div class="grid">%s</div>' % nas_cards
    return PAGE.format(
        refresh=INTERVAL,
        cluster=html.escape(CLUSTER_NAME),
        updated=now_jst(),
        summary="稼働中 %d / %d 台" % (up, len(names)),
        body=body,
        head_script=HEAD_SCRIPT,
        body_script=BODY_SCRIPT,
        theme_css=THEME_CSS,
        theme_select=THEME_SELECT,
    )


def now_jst():
    return datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S %Z")


def render_error(message):
    return PAGE.format(
        refresh=INTERVAL,
        cluster=html.escape(CLUSTER_NAME),
        updated=now_jst(),
        summary="取得失敗",
        body='<p class="error">Prometheus からの取得に失敗しました: %s</p>'
        % html.escape(message),
        head_script=HEAD_SCRIPT,
        body_script=BODY_SCRIPT,
        theme_css=THEME_CSS,
        theme_select=THEME_SELECT,
    )


def write_atomic(content):
    path = os.path.join(OUT_DIR, "index.html")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp, path)


def build_once():
    try:
        return render(collect())
    except Exception as exc:  # 取得失敗はページに表示し、次の周期で再試行する
        print("generate failed: %s" % exc, file=sys.stderr, flush=True)
        return render_error(str(exc))


def main():
    if "--once" in sys.argv:
        write_atomic(build_once())
        return
    while True:
        write_atomic(build_once())
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
