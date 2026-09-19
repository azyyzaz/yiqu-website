#!/usr/bin/env python3
"""按价值链段累加每周人时，算出收尾的真实工期。stdlib，无依赖。

用法：
    python3 sum_hours.py tasks.json
    cat tasks.json | python3 sum_hours.py -

tasks.json 格式（"每周耗时" 写数字，单位人时；"频次" 只作展示用）：

    [
      {"task": "每次发版手工跑一遍主流程回归", "segment": "联调测试", "who": "组员B", "freq": "每周", "hours": 6},
      {"task": "线上报错复现并定位",           "segment": "维护响应", "who": "值班人", "freq": "每周", "hours": 5},
      {"task": "写发版说明与变更记录",         "segment": "上线交付", "who": "组长",   "freq": "每次发版", "hours": 1.5}
    ]

如果 hours 是「每次」的量，加个 "per_week" 字段写每周发生几次，脚本会自己乘：

      {"task": "写发版说明", "segment": "上线交付", "freq": "每次发版", "hours": 1.5, "per_week": 2}
"""

import json
import sys

# 价值链段的固定顺序，也是「收尾三段」的判定依据
SEGMENTS = ["接需求", "评估排期", "设计", "编码", "联调测试", "上线交付", "维护响应"]

# 这几段就是「收尾」——它们最常被漏掉，也最常造成漂移
TAIL_SEGMENTS = {"联调测试", "上线交付", "维护响应"}

BAR = "=" * 58


def load(path):
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fmt(n):
    """整数就不显示小数点。"""
    return str(int(n)) if float(n).is_integer() else f"{n:g}"


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    try:
        tasks = load(sys.argv[1])
    except (OSError, json.JSONDecodeError) as e:
        print(f"读不了这个文件：{e}", file=sys.stderr)
        return 1

    if not isinstance(tasks, list) or not tasks:
        print("任务清单是空的。", file=sys.stderr)
        return 1

    # 逐条算每周人时
    rows = []
    unknown = []
    for i, t in enumerate(tasks, 1):
        seg = t.get("segment", "").strip()
        if seg not in SEGMENTS:
            unknown.append(seg or "(没写)")
        try:
            hours = float(t.get("hours", 0))
        except (TypeError, ValueError):
            hours = 0.0
        per_week = float(t.get("per_week", 1) or 1)
        rows.append({
            "no": i,
            "task": t.get("task", "(没写)"),
            "segment": seg,
            "who": t.get("who", "(没写)"),
            "hours": hours * per_week,
        })

    by_seg = {s: 0.0 for s in SEGMENTS}
    for r in rows:
        if r["segment"] in by_seg:
            by_seg[r["segment"]] += r["hours"]

    total = sum(by_seg.values())
    tail = sum(v for k, v in by_seg.items() if k in TAIL_SEGMENTS)

    # 分段明细
    print(BAR)
    print("按价值链段")
    print(BAR)
    for s in SEGMENTS:
        v = by_seg[s]
        if v == 0:
            continue
        mark = "  ← 收尾" if s in TAIL_SEGMENTS else ""
        print(f"  {s:<10} {fmt(v):>6} 人时/周{mark}")

    # 按人
    by_who = {}
    for r in rows:
        by_who[r["who"]] = by_who.get(r["who"], 0.0) + r["hours"]
    print()
    print(BAR)
    print("按人")
    print(BAR)
    for who, v in sorted(by_who.items(), key=lambda kv: -kv[1]):
        print(f"  {who:<10} {fmt(v):>6} 人时/周")

    # 总账
    print()
    print(BAR)
    print(f"  全部合计            {fmt(total):>6} 人时/周")
    print(f"  其中收尾三段        {fmt(tail):>6} 人时/周", end="")
    if total > 0:
        print(f"   （占 {tail / total:.0%}）")
    else:
        print()
    print(BAR)

    print()
    if tail > 0:
        print(f"收尾每周要花 {fmt(tail)} 人时。")
        print("这个数字以前不在你的排期里，所以它每次都变成「意外」。")
        print("拿去反向排期：收尾应占整个周期的 30%~40%。")
    else:
        print("没有一条任务归到收尾三段 —— 大概率是漏了，回头再拆一遍。")

    # 数据质量问题
    warnings = []
    if unknown:
        warnings.append(
            f"价值链段不认识：{'、'.join(unknown)}（只能是 {'、'.join(SEGMENTS)}）"
        )
    zero = [r for r in rows if r["hours"] == 0]
    if zero:
        warnings.append(f"{len(zero)} 条任务的耗时是 0 —— 频次和耗时必须写数字")
    one_who = [r for r in rows if r["who"] in ("大家一起", "全组", "我们")]
    if one_who:
        warnings.append(f"{len(one_who)} 条任务没有指定到个人 —— 必须是一个人做")
    if len(rows) < 5:
        warnings.append(f"只拆了 {len(rows)} 条，通常意味着拆得还不够细（目标 8~10 条）")

    if warnings:
        print()
        print("待修：")
        for w in warnings:
            print(f"  · {w}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
