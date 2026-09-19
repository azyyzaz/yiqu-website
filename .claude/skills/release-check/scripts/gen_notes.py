#!/usr/bin/env python3
"""从 git log 生成发版说明草稿。stdlib，无依赖。

用法：
    python3 gen_notes.py                    # 上一个 tag 到 HEAD
    python3 gen_notes.py v1.2.0             # v1.2.0 到 HEAD
    python3 gen_notes.py v1.2.0 v1.3.0      # 指定区间
    python3 gen_notes.py v1.2.0 HEAD --json # 输出 JSON

只起稿。发出去之前必须人工过一遍 —— 脚本不知道哪些改动对用户重要。
"""

import json
import re
import subprocess
import sys

# 提交信息前缀 -> 分组
GROUPS = [
    ("feat", "新增"),
    ("fix", "修复"),
    ("perf", "性能"),
    ("refactor", "重构"),
    ("docs", "文档"),
    ("style", "样式"),
    ("test", "测试"),
    ("chore", "杂项"),
    ("build", "构建"),
    ("ci", "CI"),
]
GROUP_OF = dict(GROUPS)

# 这些不进发版说明
SKIP_PREFIX = {"chore", "ci", "test", "style", "build"}

# 只跳过纯格式类提交，其余照收
SKIP_SUBJECTS = re.compile(r"^(wip|tmp|temp|typo|format|Merge |Revert )", re.I)

SUBJECT_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<desc>.+)$",
    re.I,
)

FIELD = "\x1f"
RECORD = "\x1e"


def git(*args):
    r = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if r.returncode != 0:
        print(r.stderr.strip() or f"git {' '.join(args)} 失败", file=sys.stderr)
        sys.exit(1)
    return r.stdout


def last_tag():
    r = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return r.stdout.strip() if r.returncode == 0 else ""


def collect(rng):
    raw = git("log", f"--pretty=format:%h{FIELD}%s{FIELD}%an{RECORD}", rng)
    out = []
    for rec in raw.split(RECORD):
        rec = rec.strip("\n")
        if not rec:
            continue
        parts = rec.split(FIELD)
        if len(parts) != 3:
            continue
        sha, subject, author = parts
        if SKIP_SUBJECTS.match(subject):
            continue
        m = SUBJECT_RE.match(subject)
        if m:
            ctype = m.group("type").lower()
            scope = m.group("scope") or ""
            desc = m.group("desc").strip()
            breaking = bool(m.group("breaking"))
        else:
            ctype, scope, desc, breaking = "other", "", subject.strip(), False
        out.append({
            "sha": sha, "type": ctype, "scope": scope,
            "desc": desc, "breaking": breaking, "author": author,
        })
    return out


def render(commits, rng):
    lines = [f"# 发版说明", ""]
    lines.append(f"**范围**　`{rng}`　·　共 {len(commits)} 条改动")
    lines.append("")

    breaking = [c for c in commits if c["breaking"]]
    if breaking:
        lines += ["## ⚠️ 破坏性变更", "", "**升级前必读：**", ""]
        for c in breaking:
            lines.append(f"- {c['desc']}　`{c['sha']}`")
        lines.append("")

    if not commits:
        lines += ["本次没有需要写进说明的改动。", ""]
        return "\n".join(lines)

    lines += ["## 改了什么", ""]
    for key, label in GROUPS:
        items = [c for c in commits if c["type"] == key]
        if not items:
            continue
        if key in SKIP_PREFIX:
            continue
        lines.append(f"**{label}**")
        for c in items:
            sc = f"**{c['scope']}**　" if c["scope"] else ""
            lines.append(f"- {sc}{c['desc']}　`{c['sha']}`")
        lines.append("")

    other = [c for c in commits if c["type"] not in GROUP_OF]
    if other:
        lines.append("**其他**")
        for c in other:
            lines.append(f"- {c['desc']}　`{c['sha']}`")
        lines.append("")

    skipped = [c for c in commits if c["type"] in SKIP_PREFIX]
    if skipped:
        lines.append(f"<details><summary>内部改动 {len(skipped)} 条（测试 / 杂项，一般不用发给需求方）</summary>")
        lines.append("")
        for c in skipped:
            lines.append(f"- {c['desc']}　`{c['sha']}`")
        lines += ["", "</details>", ""]

    lines += [
        "---",
        "",
        "## 发版前要补的三段（脚本写不了，人工填）",
        "",
        "**影响谁：**　",
        "",
        "**用户要不要做什么：**　（要清缓存？要重新登录？不用就说「无需操作」）",
        "",
        "**已知问题：**　",
        "",
    ]
    return "\n".join(lines)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv

    if len(args) >= 2:
        rng = f"{args[0]}..{args[1]}"
    elif len(args) == 1:
        rng = f"{args[0]}..HEAD"
    else:
        tag = last_tag()
        rng = f"{tag}..HEAD" if tag else "HEAD"
        if not tag:
            print("注意：仓库里没有 tag，改用最近 20 条提交。", file=sys.stderr)
            rng = "-20"

    commits = collect(rng)

    if as_json:
        json.dump({"range": rng, "commits": commits}, sys.stdout,
                  ensure_ascii=False, indent=2)
        print()
    else:
        print(render(commits, rng))
    return 0


if __name__ == "__main__":
    sys.exit(main())
