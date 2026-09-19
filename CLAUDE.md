# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 这是什么

福州易趣网络科技有限公司的企业官网。**纯静态站点：没有构建步骤、没有包管理器、没有依赖、没有测试框架、没有任何配置文件。** 改完文件刷新浏览器就能看到结果，不存在"编译"这一步。

全站只有 3 个需要维护的文件：

| 文件 | 职责 |
|---|---|
| `index.html` | 全部内容与结构（495 行，单页所有区块） |
| `assets/css/style.css` | 全部样式（985 行，含响应式与打印） |
| `assets/js/main.js` | 全部交互（482 行，原生 JS，无依赖） |

另外 `404.html`（Pages 的 404 页）、`assets/favicon.svg`、`robots.txt`、`sitemap.xml` 是配套文件，基本不用动。

## 常用命令

```bash
# 本地预览（任选其一，然后开 http://localhost:8000）
python3 -m http.server 8000
npx serve .

# 部署：push 即发布，GitHub Pages 约 1 分钟后自动重建
git push origin main
```

线上地址 <https://azyyzaz.github.io/yiqu-website/>，仓库 `azyyzaz/yiqu-website`（公开仓库 + Pages `main` / `/`）。没有 CI、没有 lint、没有测试，`git push` 就是全部发布流程。

## 改动的验证方式

没有测试套件，验证靠无头浏览器实测。环境在 `/tmp/shotenv`（**`/tmp` 会被清理，丢了就重建**）：

```bash
mkdir -p /tmp/shotenv && cd /tmp/shotenv && npm i playwright-core
```

Chromium 用 Playwright 缓存里那个：

```
~/Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing
```

注意 `playwright-core` 的页面选项是 `viewport`（不是 `viewportSize`）；用 `file://` 打开时加 `--allow-file-access-from-files`。

值得实测的几项（改交互或首屏时）：横向溢出、控制台报错、`prefers-reduced-motion` 下的表现、禁用 JS 后的表现、以及主线程耗时（CDP `Performance.getMetrics` 的 `ScriptDuration`）。

## 架构：两个关键约定

### 1. CSS 分节编号 + JS 分节编号一一对应

`style.css` 分 20 节、`main.js` 分 9 节，都用 `/* ---------- N. 名称 ---------- */` 标注。区块顺序与 `index.html` 的 `<section>` 顺序一致。**增删功能时请重编后续编号**，否则注释会指错地方——这个仓库之前删掉涟漪效果时就整体重编过一次。

改动大多能定位到某一节：首屏 → CSS 6 / JS 6，滚动入场 → CSS 15 / JS 4，卡片光带 → CSS 17 / JS 8。

### 2. CSS 自定义属性是数值的唯一来源

首屏的网格步距只在 `.hero` 上定义一次，CSS 和 JS 都从这里取，不要在 JS 里写死：

```css
.hero {
  --grid-size: 68px;   /* ::after 的静态网线 */
  --mesh-size: 6.8px;  /* 浮起细网，正好是 --grid-size 的 1/10 */
}
```

`main.js` 第 6 节通过 `getComputedStyle(hero).getPropertyValue('--mesh-size')` 读取。两张网严格嵌套（10:1），改一个必须同步考虑另一个。

## 首屏那层浮起细网（最复杂的一块）

`.hero` 里叠了 4 层，靠 z-index 分开：

| 层 | z-index | 说明 |
|---|---|---|
| `::before` | 0 | 顶部蓝色径向光晕 |
| `::after` | 1 | 静态 68px 网线，带径向遮罩 |
| `.hero-mesh` | 2 | canvas 细网，指针扫过时被托起 |
| `.hero-inner` | 3 | 实际内容 |

**为什么用 canvas 而不是 DOM**：6.8px 间距下整屏要两万多个格子，DOM 铺不下。曾经用 DOM 方块做过，从 68px 缩到 6.8px 时必须换成 canvas。

几个踩过的坑，改这块前务必知道：

- **`pointermove` 必须挂在 `window` 上**，不能挂在 `.hero` 上。挂在 hero 上的话指针一移出去事件就断了，坐标会冻结在最后一个"还在里面"的位置，循环永远以为指针没走，网格再也淡不掉。是否在首屏内由 `frame()` 每帧用 `getBoundingClientRect()` 重新判断（这样滚动把首屏移走、指针没动的情况也覆盖得到）。
- **不要加 `shadowBlur` 投影**。投影参数是按 68px 间距配的，落到 6.8px 后 16px 的模糊横跨两个多格子，相邻线的投影互相盖住，会糊成一块蓝色底衬——看起来像给浮起区铺了背景色。这个密度下投影当不了"单根线的立体感"，已去掉，只留线条。
- **不要在 `.hero-mesh` 上套 `--grid-mask`**。细网自带径向淡出，再叠一道固定遮罩只会在网上啃掉一块。
- 动画是按需启停的 `requestAnimationFrame`：指针离开就淡出并停机，静止期间脚本耗时实测为 0。别改成常驻循环。

## 全局不变量

- **所有站内路径必须是相对路径**（`assets/css/style.css`，不能写 `/assets/...`）。站点部署在 `用户名.github.io/仓库名/` 子路径下，绝对路径会 404。
- **裁横向溢出必须用 `overflow-x: clip`，不能用 `hidden`**。移动端抽屉用 `translateX(100%)` 藏在屏幕右侧之外，会撑出横向滚动；而 `hidden` 会创建滚动容器，导致顶部导航的 `position: sticky` 失效。
- **主题色改了要同步 3 处**：`style.css` 的 `:root`（`--accent` / `--accent-hover` / `--accent-soft`）、`assets/favicon.svg` 里 `<rect>` 的 `fill`、`404.html` 的内联样式。
- **每个交互都要有降级路径**：`prefers-reduced-motion`、触摸屏（`(hover: hover) and (pointer: fine)`）、以及完全禁用 JS。首屏细网、卡片光带在不满足条件时直接不初始化；`.reveal` 入场动画在无 JS 时靠 `<noscript>` 样式保持可见。加新交互时照此办理。
- 页脚年份由 JS 生成，不用每年手动改。

## 内容方面的红线

站点内容基于公开工商信息整理，**发布前有几项需要公司确认**，详见 `README.md` 的「部署前必做」一节。其中与代码直接相关的一条：

**页脚的 ICP 备案号 `闽ICP备15012597号-1` 只覆盖 `yiquwl.com`，不覆盖 `github.io` 域名。** 站点当前跑在 `azyyzaz.github.io` 上，域名与备案对不上，所以这一行**已经注释掉**（在 `index.html` 的 `.footer-legal` 里，注释中写明了恢复方法）。**绑定 `www.yiquwl.com` 之后要记得放开它**——连同它前面的分隔点 `<span class="dot">` 一起，否则会出现一个孤零零的前导 `·`。

注意「增值电信业务经营许可证 闽B2-20260993」是另一回事，那是公司持有的经营许可证编号，与域名无关，保持展示。

另外页面上**刻意没有写**员工人数、营收数据与客户案例，不要"顺手补充"这类未经确认的内容。
