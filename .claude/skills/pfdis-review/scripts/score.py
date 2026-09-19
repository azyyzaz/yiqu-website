#!/usr/bin/env python3
"""PFDIS 五维打分 —— 相乘排名，并算出最低维对应的下一步动作。stdlib，无依赖。

用法：
    python3 score.py scores.json
    cat scores.json | python3 score.py -
    python3 score.py scores.json --json
    python3 score.py scores.json --top 2        # 只输出前 2 项的详细动作

scores.json 格式：

    [
      {"task": "UI 风格贫瘠、不好看", "P": 5, "F": 5, "D": 2, "I": 2, "S": 4},
      {"task": "开发周期较长",       "P": 2, "F": 5, "D": 2, "I": 3, "S": 4}
    ]

也支持三人打分后求平均（用 pfd 数组）：

      {"task": "UI 风格", "pfd": [[5,5,2,2,4], [5,4,2,2,4], [4,5,3,2,4]]}
"""

import json
import sys

DIMS = ["P", "F", "D", "I", "S"]
DIM_NAME = {
    "P": "痛点", "F": "高频", "D": "数据", "I": "可描述", "S": "敏感度",
}

# 最低维 -> 固定动作（和 references/dimensions.md 保持一致）
ACTION = {
    "P": "这件事还不够痛，先放着，别浪费人力",
    "F": "频次太低，不值得为它建流程，临时处理即可",
    "D": "先归集数据，再上 AI —— 这是最常见的形态",
    "I": "先把流程和标准写成文字，写不出来就说明还没想清楚",
    "S": "AI 帮不上忙，换个思路，别硬套",
}

BAR = "=" * 66


def load(path):
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dims_of(item):
    """取出五维分数。支持直接给 P/F/D/I/S，或给 pfd 数组求平均（四舍五入）。"""
    if all(d in item for d in DIMS):
        out = {}
        for d in DIMS:
            try:
                out[d] = int(item[d])
            except (TypeError, ValueError):
                return None, f"{d} 不是整数：{item[d]!r}"
        return out, None

    if "pfd" in item:
        rows = item["pfd"]
        if not isinstance(rows, list) or not rows:
            return None, "pfd 是空的"
        out = {}
        for i, d in enumerate(DIMS):
            vals = []
            for r in rows:
                if not isinstance(r, list) or len(r) != 5:
                    return None, "pfd 里每一行都必须是 5 个数字"
                vals.append(float(r[i]))
            out[d] = int(round(sum(vals) / len(vals)))
        return out, None

    return None, "既没有 P/F/D/I/S，也没有 pfd"


def main():
    argv = sys.argv[1:]
    as_json = "--json" in argv
    top = None
    if "--top" in argv:
        try:
            top = int(argv[argv.index("--top") + 1])
        except (IndexError, ValueError):
            print("--top 后面要跟一个数字", file=sys.stderr)
            return 1

    args = [a for a in argv if not a.startswith("--")]
    if "--top" in argv:
        args = [a for a in args if not a.isdigit()]
    if len(args) != 1:
        print(__doc__)
        return 2

    try:
        items = load(args[0])
    except (OSError, json.JSONDecodeError) as e:
        print(f"读不了这个文件：{e}", file=sys.stderr)
        return 1

    if not isinstance(items, list) or not items:
        print("打分表是空的。", file=sys.stderr)
        return 1

    results, errors = [], []
    for i, item in enumerate(items, 1):
        name = item.get("task") or item.get("name") or f"(第 {i} 条)"
        d, err = dims_of(item)
        if err:
            errors.append(f"{name}：{err}")
            continue
        bad = [k for k, v in d.items() if not 1 <= v <= 5]
        if bad:
            errors.append(f"{name}：{'、'.join(bad)} 超出 1–5 的范围")
            continue
        total = 1
        for k in DIMS:
            total *= d[k]
        weakest = min(DIMS, key=lambda k: (d[k], DIMS.index(k)))
        results.append({
            "task": name, "dims": d, "total": total,
            "weakest": weakest, "weakest_score": d[weakest],
            "weakest_all": [k for k in DIMS if d[k] == d[weakest]],
        })

    if errors:
        print("这些问题得先修：", file=sys.stderr)
        for e in errors:
            print(f"  · {e}", file=sys.stderr)
        if not results:
            return 1

    results.sort(key=lambda r: -r["total"])

    if as_json:
        json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0

    # ---- 排名表 ----
    print(BAR)
    print("PFDIS 排名")
    print(BAR)
    print(f"  {'#':<3}{'任务':<26}{'P':>3}{'F':>3}{'D':>3}{'I':>3}{'S':>3}{'总分':>8}   最低维")
    print("  " + "-" * (len(BAR) - 4))
    for i, r in enumerate(results, 1):
        d = r["dims"]
        w = "/".join(f"{k}={d[k]}" for k in r["weakest_all"])
        print(f"  {i:<3}{r['task'][:24]:<26}"
              f"{d['P']:>3}{d['F']:>3}{d['D']:>3}{d['I']:>3}{d['S']:>3}"
              f"{r['total']:>8}   {w}")
    print(BAR)

    # ---- 拟切入点 ----
    n = top or min(2, len(results))
    n = max(1, min(n, len(results)))
    print()
    print(BAR)
    print(f"拟切入点（取前 {n} 项）")
    print(BAR)
    for i, r in enumerate(results[:n], 1):
        d = r["dims"]
        expr = "×".join(str(d[k]) for k in DIMS)
        print(f"  {i}. {r['task']}　（{expr} = {r['total']}）")
        # 最低维可能并列，逐条给动作
        for k in r["weakest_all"]:
            print(f"       最低维：{k} {DIM_NAME[k]} = {d[k]}")
            print(f"       下一步：{ACTION[k]}")
        print()

    # ---- 不进这轮的 ----
    rest = results[n:]
    if rest:
        print(BAR)
        print(f"这一轮不做（{len(rest)} 项，进下一轮）")
        print(BAR)
        for r in rest:
            print(f"  · {r['task']}（{r['total']} 分）—— {ACTION[r['weakest']]}")
        print()

    # ---- 纪律提醒 ----
    notes = []
    if len(results) > 3:
        notes.append(f"候选有 {len(results)} 项，只取前 {n} 项 —— 3 个人的组同时推 2 项已经是上限")
    for r in results[:n]:
        if r["weakest"] == "P":
            notes.append(
                f"「{r['task']}」的最低维是 P（痛点 = {r['dims']['P']}）—— "
                f"总分是靠其他维度撑起来的，但痛点本身不高。"
                f"确认一下是不是真的要现在做；如果确实是，说明 P 打低了"
            )
        if r["dims"]["D"] <= 2 and r["weakest"] == "D":
            notes.append(f"「{r['task']}」的 D 维度偏低，打分前请真的打开那个文件/系统确认一遍")
    if any(r["dims"]["S"] >= 4 and r["dims"]["I"] <= 2 for r in results):
        notes.append("有任务 S 高但 I 低 —— 效果明显却说不清标准，先补 I 再上")
    if notes:
        print(BAR)
        print("待确认")
        print(BAR)
        for x in notes:
            print(f"  · {x}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
