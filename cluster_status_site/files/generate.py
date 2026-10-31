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


def collect():
    data = {
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


PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="{refresh}">
<title>{cluster} Cluster Status</title>
<style>
  :root {{
    --bg: #f6f7f9; --card: #ffffff; --text: #1d232b; --muted: #6b7280;
    --line: #e3e6eb; --track: #e5e7eb; --ok: #15803d; --warn: #b45309; --crit: #b91c1c;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg: #0f1419; --card: #1a2029; --text: #e6e9ef; --muted: #9aa4b2;
      --line: #2a323d; --track: #2f3742; --ok: #4ade80; --warn: #fbbf24; --crit: #f87171;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg: #0f1419; --card: #1a2029; --text: #e6e9ef; --muted: #9aa4b2;
    --line: #2a323d; --track: #2f3742; --ok: #4ade80; --warn: #fbbf24; --crit: #f87171;
  }}
  body {{ font-family: system-ui, sans-serif; margin: 16px; background: var(--bg); color: var(--text); }}
  h1 {{ font-size: 22px; margin: 0 0 4px; }}
  h2 {{ font-size: 17px; margin: 0; }}
  .note {{ color: var(--muted); font-size: 13px; margin: 0 0 16px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }}
  .card {{ background: var(--card); border: 1px solid var(--line); border-top: 4px solid var(--crit); border-radius: 10px; padding: 12px 14px; }}
  .card.ok {{ border-top-color: var(--ok); }}
  .card header {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; }}
  .badge {{ font-size: 12px; font-weight: bold; padding: 2px 8px; border-radius: 999px; color: #fff; white-space: nowrap; }}
  .badge.ok {{ background: var(--ok); }}
  .badge.down {{ background: var(--crit); }}
  .meta {{ color: var(--muted); font-size: 12px; margin: 6px 0 0; }}
  .row {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 13px; margin-top: 10px; }}
  .muted {{ color: var(--muted); font-size: 12px; }}
  .meter {{ height: 6px; background: var(--track); border-radius: 3px; overflow: hidden; margin-top: 4px; }}
  .fill {{ height: 100%; }}
  .fill.ok {{ background: var(--ok); }}
  .fill.warn {{ background: var(--warn); }}
  .fill.crit {{ background: var(--crit); }}
  .spark {{ width: 160px; height: 36px; color: var(--ok); flex-shrink: 0; }}
  .error {{ background: #fdecea; color: #7f1d1d; border: 1px solid #b91c1c; padding: 8px; border-radius: 8px; }}
</style>
</head>
<body>
<h1>{cluster} Cluster Status</h1>
<p class="note">最終更新: {updated}(約 {refresh} 秒ごとに更新) / {summary}</p>
{body}
</body>
</html>
"""


def render(data):
    names = sorted(data["seen"].keys())
    up = sum(1 for name in names if status_of(name, data)[1] == "ok")
    cards = "".join(render_card(name, data) for name in names)
    return PAGE.format(
        refresh=INTERVAL,
        cluster=html.escape(CLUSTER_NAME),
        updated=now_jst(),
        summary="稼働中 %d / %d 台" % (up, len(names)),
        body='<div class="grid">%s</div>' % cards,
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
