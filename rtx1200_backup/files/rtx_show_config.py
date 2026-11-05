#!/usr/bin/env python3
"""Yamaha RTX の show config を読み取り専用で取得し、保存先に 0600 で書き出す。

使い方: rtx_show_config.py <ホスト> <ユーザー> <保存先ディレクトリ>
パスワードは環境変数 SSHPASS から sshpass -e で渡す(引数・表示には出さない)。
設定の内容は標準出力に表示しない。表示するのは保存先パスと行数だけ。
"""
import os
import re
import select
import subprocess
import sys
import time
from datetime import datetime

SSH_OPTIONS = [
    "-o", "ConnectTimeout=10",
    "-o", "UserKnownHostsFile=/dev/null",
    "-o", "StrictHostKeyChecking=no",
    # RTX は古い鍵交換方式(SHA-1)と ssh-rsa しか提示しないため、互換オプションを有効にする
    "-o", "KexAlgorithms=+diffie-hellman-group14-sha1,diffie-hellman-group1-sha1",
    "-o", "HostKeyAlgorithms=+ssh-rsa",
    "-o", "PubkeyAcceptedAlgorithms=+ssh-rsa",
    "-o", "PubkeyAuthentication=no",
]


def read_for(proc, seconds, until_prompt=False):
    out = b""
    end = time.time() + seconds
    while time.time() < end:
        ready, _, _ = select.select([proc.stdout], [], [], 0.3)
        if ready:
            chunk = os.read(proc.stdout.fileno(), 65536)
            if not chunk:
                break
            out += chunk
            if b"--More--" in chunk:
                proc.stdin.write(b" ")
                proc.stdin.flush()
            if until_prompt and re.search(rb"\r?\n> ?$", out):
                break
    return out


def fetch_config(host, user):
    cmd = ["sshpass", "-e", "ssh", "-tt", *SSH_OPTIONS, f"{user}@{host}"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    read_for(proc, 4)
    proc.stdin.write(b"show config\r\n")
    proc.stdin.flush()
    raw = read_for(proc, 60, until_prompt=True)
    proc.stdin.write(b"exit\r\n")
    proc.stdin.flush()
    read_for(proc, 2)
    proc.kill()
    return raw


def clean(raw):
    text = raw.decode(errors="replace")
    text = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text).replace("\r", "")
    text = text.replace("--More--", "")
    lines = text.split("\n")
    if lines and lines[0].strip().startswith("show config"):
        lines = lines[1:]
    while lines and lines[-1].strip() in (">", ""):
        lines.pop()
    return lines


def main():
    if len(sys.argv) != 4:
        print("usage: rtx_show_config.py <host> <user> <backup_dir>", file=sys.stderr)
        return 2
    host, user, backup_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    if "SSHPASS" not in os.environ:
        print("SSHPASS が設定されていません", file=sys.stderr)
        return 2

    lines = clean(fetch_config(host, user))
    # 失敗時(エラー応答・空応答)は保存しない。内容は表示しない
    if len(lines) < 5 or any(l.startswith(("Error", "Invalid")) for l in lines[:3]):
        print("取得に失敗したため保存しませんでした(応答の行数: %d)" % len(lines), file=sys.stderr)
        return 1

    body = "\n".join(lines).strip() + "\n"
    os.makedirs(backup_dir, mode=0o700, exist_ok=True)
    os.chmod(backup_dir, 0o700)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(backup_dir, f"{host}-{stamp}.cfg")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(body)
    print(f"saved: {path} lines: {body.count(chr(10))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
