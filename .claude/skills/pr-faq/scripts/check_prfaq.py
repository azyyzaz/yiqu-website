#!/usr/bin/env python3
"""检查一份 PR/FAQ 够不够格通过关卡 G1「需求冻结」。stdlib，无依赖。

用法：
    python3 check_prfaq.py docs/pr-faq/<项目名>.md

它查四件事：
  1. 未来时态词 —— 通篇必须是「已经上线」的口吻，不是「计划做」
  2. 待定词     —— 五个 FAQ 不许留「待定」「再议」
  3. 五问齐不齐 —— 每问下面必须有答案，只有标题不算
  4. 有没有引言 —— 新闻稿里得有用户原话，且不能是占位符

退出码：0 = 可以过 G1；1 = 有问题；2 = 用法错

会跳过 ``` 围起来的代码块，所以规则说明抄进文件里也不会误报。
"""

import re
import sys
import unicodedata

BAR = "=" * 58

# 一定算未来时态的
HARD_FUTURE = ["计划", "未来", "打算", "后续", "预计", "将要", "即将",
               "届时", "争取", "目标是", "预期", "愿景"]

# 作介词时是「把」的意思（将数据导出 = 把数据导出），要人眼确认
SOFT = {
    "将": {"before": "即", "after": "军来"},
    "会": {"before": "机议学体不社协工商年理领委展览餐聚"},
}

# 出现在哪一行都算没写完
PENDING = ["待定", "再议", "TBD", "tbd", "待确认", "待补充", "暂定",
           "后续讨论", "还没想好", "看情况"]

# 编的引言会在这些字样上露馅
PLACEHOLDER = ["某某", "XX", "xx", "XXX", "＜", "待填", "某公司", "某位"]

FAQ_HEAD = re.compile(r"^##\s*(常见问题|FAQ|常见问题解答)\s*$")
H2 = re.compile(r"^##\s+")
NUM_ITEM = re.compile(r"^\s*(\d+)\s*[.、)）]\s*(.*\S)")
QUOTE = re.compile(r"[「“\"]")


def width(s):
    """显示宽度：汉字和全角标点占两列。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s, n, cut=None):
    """按显示宽度补齐到 n 列；cut 是允许的最大宽度，超了截断加省略号。"""
    if cut and width(s) > cut:
        out, w = "", 0
        for c in s:
            cw = 2 if unicodedata.east_asian_width(c) in "WF" else 1
            if w + cw > cut - 1:
                break
            out, w = out + c, w + cw
        s = out + "…"
    return s + " " * max(0, n - width(s))


def strip_fences(lines):
    """抹掉 ``` 代码块的内容（保留行号），免得规则说明被当成正文。"""
    out, in_fence = [], False
    for ln in lines:
        if ln.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else ln)
    return out


def find_section(lines, head_re):
    """返回 (起, 止) 行号区间，止为下一个 ## 之前。找不到返回 None。"""
    start = None
    for i, ln in enumerate(lines):
        if head_re.match(ln):
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        if H2.match(lines[j]):
            end = j
            break
    return start, end


def check_future(lines):
    hits, soft = [], []
    for i, ln in enumerate(lines, 1):
        for w in HARD_FUTURE:
            if w in ln:
                hits.append((i, w, ln.strip()))
        for w, rule in SOFT.items():
            for m in re.finditer(re.escape(w), ln):
                p = m.start()
                if p > 0 and ln[p - 1] in rule.get("before", ""):
                    continue
                if p + 1 < len(ln) and ln[p + 1] in rule.get("after", ""):
                    continue
                soft.append((i, w, ln.strip()))
                break
    return hits, soft


def check_pending(lines):
    return [(i, w, ln.strip())
            for i, ln in enumerate(lines, 1)
            for w in PENDING if w in ln]


def check_faq(lines):
    """返回 [(序号, 问题, 答案行数)]，以及「有没有找到 FAQ 段」。"""
    sec = find_section(lines, FAQ_HEAD)
    if sec is None:
        return None, False
    start, end = sec
    items, cur = [], None
    for ln in lines[start:end]:
        m = NUM_ITEM.match(ln)
        if m:
            cur = {"no": int(m.group(1)), "q": m.group(2), "answers": []}
            items.append(cur)
        elif cur is not None and ln.strip():
            cur["answers"].append(ln.strip())
    return items, True


def check_quote(lines):
    sec = find_section(lines, re.compile(r"^##\s*新闻稿\s*$"))
    if sec is None:
        return False, []
    start, end = sec
    body = "\n".join(lines[start:end])
    if not QUOTE.search(body):
        return False, []
    return True, [w for w in PLACEHOLDER if w in body]


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read().splitlines()
    except OSError as e:
        print(f"读不了这个文件：{e}", file=sys.stderr)
        return 1

    if not raw:
        print("文件是空的。", file=sys.stderr)
        return 1

    lines = strip_fences(raw)
    todo = []

    print(BAR)
    print(f"PR/FAQ 自检 —— {path}")
    print(BAR)

    # ---- 1. 未来时态 ----
    hits, soft = check_future(lines)
    print()
    print("【1】未来时态词")
    if hits:
        print("  硬命中（必须改）：")
        for i, w, ln in hits[:12]:
            print(f"    第 {i} 行  「{w}」  {ln[:46]}")
        if len(hits) > 12:
            print(f"    …… 还有 {len(hits) - 12} 处")
        todo.append(f"{len(hits)} 处未来时态词，新闻稿必须是「已经上线」的口吻")
    else:
        print("  ✓ 没有未来时态词")
    if soft:
        print("  软命中（「将」也可能是「把」，「会」也可能是「机会」，人眼扫一遍）：")
        for i, w, ln in soft[:8]:
            print(f"    第 {i} 行  「{w}」  {ln[:46]}")
        if len(soft) > 8:
            print(f"    …… 还有 {len(soft) - 8} 处")

    # ---- 2. 待定词 ----
    pend = check_pending(lines)
    print()
    print("【2】待定词")
    if pend:
        for i, w, ln in pend[:12]:
            print(f"  ✗ 第 {i} 行  「{w}」  {ln[:44]}")
        todo.append(f"{len(pend)} 处「待定」类字样 —— 五问都必须有答案")
    else:
        print("  ✓ 没有待定词")

    # ---- 3. 五个 FAQ ----
    items, found = check_faq(lines)
    print()
    print("【3】五个 FAQ")
    if not found:
        print("  ✗ 找不到「## 常见问题」这一段")
        todo.append("缺「## 常见问题」段落")
    else:
        if len(items) != 5:
            todo.append(f"FAQ 是 {len(items)} 问，模板要求 5 问")
        blank, vague = [], []
        for it in items:
            n = len(it["answers"])
            body = " ".join(it["answers"])
            # 有答案行、但答案本身是「待定」这类空话 —— 不算答了
            hollow = [w for w in PENDING if w in body]
            if not n:
                mark, tail, blank = "✗", "没有答案", blank + [it["no"]]
            elif hollow:
                mark, tail, vague = "⚠", f"答案是「{hollow[0]}」，等于没答", vague + [it["no"]]
            else:
                mark, tail = "✓", f"有答案（{n} 行）"
            print(f"  {mark} {it['no']}. {pad(it['q'], 30, cut=30)} {tail}")
        if blank:
            todo.append(f"FAQ 第 {'、'.join(map(str, blank))} 问没有答案")
        if vague:
            todo.append(f"FAQ 第 {'、'.join(map(str, vague))} 问只写了「待定」这类空话")

    # ---- 4. 引言 ----
    has_q, ph = check_quote(lines)
    print()
    print("【4】引言")
    if not has_q:
        print("  ✗ 新闻稿里没有用户引言")
        todo.append("新闻稿缺用户引言 —— 问不到就写「这句还没问到」，不要编")
    elif ph:
        print(f"  ✗ 引言里出现占位符：{'、'.join(ph)} —— 还是模板，没换成真话")
        todo.append("引言还是占位符，必须换成真实的话或明确写「还没问到」")
    else:
        print("  ✓ 有引言，且看不出占位符")

    # ---- 结论 ----
    print()
    print(BAR)
    if todo:
        print(f"结论：不能过 G1（{len(todo)} 项待修）")
    else:
        print("结论：可以过 G1")
    print(BAR)
    for t in todo:
        print(f"  · {t}")
    if not todo:
        print("  → 交给组长核；组长是提案人时，交任一未参与的组员核。")
    return 1 if todo else 0


if __name__ == "__main__":
    sys.exit(main())
