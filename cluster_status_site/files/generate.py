#!/usr/bin/env python3
"""Prometheus の値から静的なステータスページ(index.html)を作り直す。

標準ライブラリだけを使う。INTERVAL 秒ごとに作り直し、書き出しは一時ファイル経由で
行うため、配信側(nginx)は途中まで書かれたページを読まない。
取得に失敗した場合は、エラーを表示したページに置き換える。
"""
import html
import json
import os
import sys
import time
import urllib.parse
import urllib.request

PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://127.0.0.1:9090").rstrip("/")
INTERVAL = int(os.environ.get("INTERVAL", "60"))
CLUSTER_NAME = os.environ.get("CLUSTER_NAME", "JARVIS")
OUT_DIR = os.environ.get("OUT_DIR", "/site")
TIMEOUT = 10

# 表示するファイルシステム(tmpfs や overlay などは除外する)
FS_TYPES = "ext4|xfs|btrfs|zfs|vfat|nfs.*"
JOB = 'job="node_exporter"'


def query(promql):
    url = PROMETHEUS_URL + "/api/v1/query?" + urllib.parse.urlencode({"query": promql})
    with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
        body = json.load(resp)
    if body.get("status") != "success":
        raise RuntimeError("Prometheus クエリに失敗しました: " + promql)
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


def render_row(name, data):
    label, css = status_of(name, data)
    cells = [html.escape(name), '<span class="%s">%s</span>' % (css, label)]
    if name in data["load1"]:
        cells.append("%.2f" % data["load1"][name])
    else:
        cells.append("-")
    cells.append(str(int(data["cores"][name])) if name in data["cores"] else "-")
    if name in data["mem_total"] and name in data["mem_avail"]:
        total = data["mem_total"][name]
        used_pct = (1 - data["mem_avail"][name] / total) * 100
        cells.append("%.0f%%" % used_pct)
        cells.append(fmt_gib(total))
    else:
        cells.extend(["-", "-"])
    if name in data["boot"]:
        cells.append(fmt_uptime(time.time() - data["boot"][name]))
    else:
        cells.append("-")
    cells.append(html.escape(data["kernel"].get(name, "-")))
    disk_lines = []
    for mount, avail, size in sorted(data["disks"].get(name, [])):
        disk_lines.append(
            "%s: %s / %s" % (html.escape(mount), fmt_gib(avail), fmt_gib(size))
        )
    cells.append("<br>".join(disk_lines) or "-")
    return "<tr>" + "".join("<td>%s</td>" % c for c in cells) + "</tr>"


PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="{refresh}">
<title>{cluster} Cluster Status</title>
<style>
  body {{ font-family: sans-serif; margin: 16px; background: #fafafa; color: #222; }}
  table {{ border-collapse: collapse; width: 100%; background: #fff; }}
  th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: left; vertical-align: top; font-size: 14px; }}
  th {{ background: #f0f0f0; }}
  .ok {{ color: #0a7d32; font-weight: bold; }}
  .down {{ color: #b00020; font-weight: bold; }}
  .error {{ background: #fdecea; border: 1px solid #b00020; padding: 8px; }}
  .note {{ color: #666; font-size: 13px; }}
  @media (max-width: 720px) {{ table, thead, tbody, tr, th, td {{ display: block; }} thead {{ display: none; }} td {{ border: none; padding: 2px 8px; }} tr {{ border-bottom: 1px solid #ddd; padding: 6px 0; background: #fff; }} }}
</style>
</head>
<body>
<h1>{cluster} Cluster Status</h1>
<p class="note">最終更新: {updated}(約 {refresh} 秒ごとに更新)</p>
{body}
</body>
</html>
"""

HEADERS = (
    "<tr><th>ホスト</th><th>状態</th><th>Load (1m)</th><th>CPU コア</th>"
    "<th>メモリ使用率</th><th>メモリ総量</th><th>稼働時間</th><th>カーネル</th>"
    "<th>ディスク(使用可能 / 総量)</th></tr>"
)


def render(data):
    names = sorted(data["seen"].keys())
    rows = "".join(render_row(name, data) for name in names)
    table = "<table><thead>%s</thead><tbody>%s</tbody></table>" % (HEADERS, rows)
    return PAGE.format(
        refresh=INTERVAL,
        cluster=html.escape(CLUSTER_NAME),
        updated=time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        body=table,
    )


def render_error(message):
    return PAGE.format(
        refresh=INTERVAL,
        cluster=html.escape(CLUSTER_NAME),
        updated=time.strftime("%Y-%m-%d %H:%M:%S %Z"),
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
