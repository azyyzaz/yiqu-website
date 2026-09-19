#!/usr/bin/env python3
"""检查一份接口契约够不够格通过关卡 G2「方案定稿」。stdlib，无依赖。

用法：
    python3 check_contract.py docs/contract/<项目名>.md

它查四件事：
  1. 每个接口的五要素齐不齐 —— 路径 / 字段与类型 / 错误码 / 边界情况 / 示例
  2. 边界清单覆盖了几条     —— 十条常见边界，见 references/boundaries.md
  3. 签字栏                 —— 提出方与对接方是否都有名字和日期
  4. 变更记录               —— 有就报几条，没有不算错

退出码：0 = 可以过 G2；1 = 有问题；2 = 用法错

注意：**边界覆盖率是提示，不是判定。** 它只负责提醒你别漏；
没覆盖到不等于不需要，覆盖到了也不等于写对了。
"""

import re
import sys

BAR = "=" * 58

# 接口声明：## GET /api/x  或  顶格的 GET /api/x
# 必须带 # 或顶格 —— 否则「示例」段里缩进的那行   POST /api/x
# 会被当成一个新的接口声明，接口数就多出来了。
METHODS = "GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS"
IFACE = re.compile(
    rf"^(?:\s*#{{1,4}}\s*(?P<m1>{METHODS})|(?P<m2>{METHODS}))\s+(?P<path>/\S+)", re.I)
H2 = re.compile(r"^\s*#{2,4}\s+")


def iface_of(ln):
    """这一行是不是接口声明？是就返回 (方法, 路径)。"""
    m = IFACE.match(ln)
    if not m:
        return None
    return (m.group("m1") or m.group("m2")).upper(), m.group("path")

# 字段类型标注的证据
TYPES = re.compile(
    r"\b(string|int|integer|number|float|double|bool|boolean|array|object|"
    r"list|date|datetime|timestamp|uuid|decimal)\b", re.I)

# 错误码
ERRCODE = re.compile(r"\b([45]\d{2})\b")

BOUNDARY_HEAD = re.compile(r"边界|异常路径|异常情况")
EXAMPLE_HEAD = re.compile(r"示例|例子|请求与响应")

# 十条常见边界，关键词取「一出现就基本能确定提到了」的
BOUNDARIES = [
    ("结果为空",      ["为空", "空数组", "空列表", "没有数据", "无数据", "[]"]),
    ("条数上限/分页",  ["分页", "上限", "最多", "limit", "page", "条数"]),
    ("参数非法",      ["非法", "不合法", "格式错", "校验失败", "INVALID", "参数错"]),
    ("权限不足",      ["权限", "未登录", "未授权", "403", "401", "FORBIDDEN"]),
    ("重复提交/幂等",  ["幂等", "去重", "重复提交", "Idempotency", "request_id"]),
    ("超时与重试",    ["超时", "重试", "timeout", "retry"]),
    ("并发",          ["并发", "冲突", "409", "CONFLICT", "乐观锁", "version"]),
    ("时间与时区",    ["时区", "UTC", "timezone", "ISO 8601", "ISO8601"]),
    ("特殊字符/编码",  ["编码", "BOM", "转义", "特殊字符", "UTF", "emoji", "CSV"]),
    ("部分成功",      ["部分成功", "批量", "逐条", "回滚", "succeeded", "failed"]),
]

SIGN_HEAD = re.compile(r"^\s*#{2,4}\s*(签字|签名|确认)")
CHANGE_HEAD = re.compile(r"^\s*#{2,4}\s*(变更|变更单|修订)")
SIGN_LABEL = re.compile(r"(提出方|对接方|签名|签字|日期|代签)")
UNDERSCORE = re.compile(r"[_＿]{2,}|[·．.]{4,}")
DATE = re.compile(r"\d{4}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2}")


def width(s):
    """显示宽度：汉字和全角标点占两列。"""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s, n, cut=None):
    import unicodedata
    if cut and width(s) > cut:
        out, w = "", 0
        for c in s:
            cw = 2 if unicodedata.east_asian_width(c) in "WF" else 1
            if w + cw > cut - 1:
                break
            out, w = out + c, w + cw
        s = out + "…"
    return s + " " * max(0, n - width(s))


def split_blocks(lines):
    """按接口声明切块。块在下一个非接口的 ## 标题处结束。"""
    starts = [i for i, ln in enumerate(lines) if iface_of(ln)]
    out = []
    for k, s in enumerate(starts):
        end = len(lines)
        for j in range(s + 1, len(lines)):
            if iface_of(lines[j]) or (H2.match(lines[j]) and not iface_of(lines[j])):
                end = j
                break
        out.append((s, end))
    return out


def section(lines, head_re):
    """返回某段落的正文行。"""
    for i, ln in enumerate(lines):
        if head_re.match(ln):
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if H2.match(lines[j]):
                    end = j
                    break
            return lines[i:end]
    return []


def check_sig(lines):
    """返回 [(行文本, 有没有名字, 有没有日期)]。"""
    out = []
    for ln in section(lines, SIGN_HEAD):
        if ln.lstrip().startswith("#"):      # 跳过「## 签字」这个标题本身
            continue
        if not SIGN_LABEL.search(ln):
            continue
        body = UNDERSCORE.sub(" ", ln)
        body = SIGN_LABEL.sub(" ", body)
        name = re.search(r"[一-龥A-Za-z]{2,}", body)
        out.append((ln.strip(), bool(name), bool(DATE.search(ln))))
    return out


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError as e:
        print(f"读不了这个文件：{e}", file=sys.stderr)
        return 1

    if not lines:
        print("文件是空的。", file=sys.stderr)
        return 1

    blocks = split_blocks(lines)
    todo = []

    print(BAR)
    print(f"接口契约自检 —— {path}")
    print(BAR)

    if not blocks:
        print()
        print("找不到任何接口声明。")
        print("每条接口写成：  ## GET /api/xxx")
        print()
        print(BAR)
        print("结论：不能过 G2")
        print(BAR)
        print("  · 文件里没有可识别的接口块")
        return 1

    print()
    print(f"找到 {len(blocks)} 个接口")

    all_body = []
    for n, (s, e) in enumerate(blocks, 1):
        head = lines[s].strip().lstrip("#").strip()
        body = lines[s:e]
        all_body.extend(body)
        blob = "\n".join(body)

        codes = sorted(set(ERRCODE.findall(blob)))
        checks = [
            ("路径",      head.startswith(tuple(m + " " for m in METHODS.split("|"))) or "/" in head, head),
            ("字段与类型", bool(TYPES.search(blob)), "找到类型标注" if TYPES.search(blob) else "没找到 string/int/array 这类类型"),
            ("错误码",    bool(codes), "、".join(codes) if codes else "没找到 4xx / 5xx"),
            ("边界情况",  bool(BOUNDARY_HEAD.search(blob)), "有边界段" if BOUNDARY_HEAD.search(blob) else "缺「边界」段"),
            ("示例",      bool(EXAMPLE_HEAD.search(blob)), "有示例" if EXAMPLE_HEAD.search(blob) else "缺「示例」段"),
        ]

        print()
        print(f"【接口 {n}】{head}")
        for name, ok, detail in checks:
            print(f"  {'✓' if ok else '✗'} {pad(name, 14)} {detail}")

        missing = [name for name, ok, _ in checks if not ok]
        if missing:
            todo.append(f"接口 {n}（{head}）缺：{'、'.join(missing)}")

    # ---- 边界清单覆盖 ----
    blob = "\n".join(all_body)
    covered, absent = [], []
    for name, kws in BOUNDARIES:
        (covered if any(k in blob for k in kws) else absent).append(name)

    print()
    print(BAR)
    print(f"边界清单覆盖：{len(covered)}/{len(BOUNDARIES)}")
    print(BAR)
    if covered:
        print(f"  已提到  {' · '.join(covered)}")
    if absent:
        print(f"  没提到  {' · '.join(absent)}")
        print()
        print("  ↑ 没提到不等于不需要。逐条过一遍 references/boundaries.md，")
        print("    不适用的在文件里写明「不适用，因为…」。")

    # ---- 签字 ----
    sigs = check_sig(lines)
    print()
    print(BAR)
    print("签字")
    print(BAR)
    if not sigs:
        print("  ✗ 找不到「## 签字」段落")
        todo.append("缺「## 签字」段落 —— 提出方与对接方各签一次")
    else:
        unsigned = []
        for ln, has_name, has_date in sigs:
            if has_name and has_date:
                print(f"  ✓ {pad(ln, 46, cut=46)}")
            else:
                lack = "、".join(x for x, ok in
                                 (("名字", has_name), ("日期", has_date)) if not ok)
                print(f"  ✗ {pad(ln, 46, cut=46)} 缺{lack}")
                unsigned.append(lack)
        if unsigned:
            todo.append("签字栏没填完整（缺名字或日期）")

    # ---- 变更记录 ----
    chg = section(lines, CHANGE_HEAD)
    if chg:
        n = sum(1 for ln in chg[1:] if DATE.search(ln))
        print()
        print(f"  变更记录：{n} 条")

    # ---- 结论 ----
    print()
    print(BAR)
    if todo:
        print(f"结论：不能过 G2（{len(todo)} 项待修）")
    else:
        print("结论：可以过 G2")
    print(BAR)
    for t in todo:
        print(f"  · {t}")
    if not todo:
        print("  → 双方都签完才算过。过门之后改契约走变更单，不要直接改文件。")
    return 1 if todo else 0


if __name__ == "__main__":
    sys.exit(main())
