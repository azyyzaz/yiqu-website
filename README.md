# 福州易趣网络科技有限公司 — 官网

企业官网静态站点。纯 HTML / CSS / JavaScript，**无构建步骤、无第三方依赖、无网络字体**，可直接托管在 GitHub Pages（免费）。

设计风格参考 [deepseek.com](https://www.deepseek.com/)：极简、留白、单栏主结构、克制的蓝色点缀。

---

## 目录结构

```
.
├── index.html              首页（全部内容区块）
├── 404.html                GitHub Pages 自定义 404 页
├── robots.txt              搜索引擎抓取规则
├── sitemap.xml             站点地图
├── .nojekyll               告诉 GitHub Pages 跳过 Jekyll 处理
└── assets/
    ├── css/style.css       全部样式（含设计变量、响应式、打印样式）
    ├── js/main.js          导航抽屉、滚动动画、导航高亮
    └── favicon.svg         站点图标
```

全站只有 3 个需要维护的文件：`index.html`（内容）、`style.css`（样式）、`main.js`（交互）。

---

## 本地预览

任选一种方式，在项目目录下执行：

```bash
# 方式一：Python（macOS / Linux 自带）
python3 -m http.server 8000

# 方式二：Node.js
npx serve .
```

然后浏览器打开 <http://localhost:8000>。

> 直接双击 `index.html` 用 `file://` 打开也能看，但部分浏览器的本地文件安全策略会影响脚本行为，建议用上面的方式。

---

## 部署到 GitHub Pages

### 第一步：在 GitHub 上新建仓库

1. 登录 GitHub，点右上角 **+** → **New repository**
2. **Repository name** 填 `yiquwl` 或 `website`（任意名字，下文以 `website` 为例）
3. 可见性选 **Public**（免费账号的 Pages 只支持公开仓库）
4. **不要**勾选 "Add a README file" / .gitignore / license —— 本地已经有了
5. 点 **Create repository**

### 第二步：把本地文件推上去

在项目目录下执行（把 `你的用户名` 换成实际的 GitHub 用户名）：

```bash
git remote add origin https://github.com/你的用户名/website.git
git branch -M main
git push -u origin main
```

### 第三步：开启 Pages

1. 进入仓库页面 → **Settings**
2. 左侧菜单拉到 **Pages**
3. **Source** 选 `Deploy from a branch`
4. **Branch** 选 `main`，目录选 `/ (root)`，点 **Save**
5. 等 1–2 分钟，页面顶部会出现访问地址：

```
https://你的用户名.github.io/website/
```

之后每次 `git push`，站点会在 1 分钟左右自动更新。

---

## 绑定自定义域名（可选，推荐）

你们已有 `yiquwl.com`，绑上去会比 `github.io/website` 更正式。

1. **仓库 Settings → Pages → Custom domain** 填入 `www.yiquwl.com`，点 Save
   （这一步会自动在仓库根目录生成 `CNAME` 文件）
2. 到域名 DNS 服务商处添加解析记录：

   | 类型 | 主机记录 | 记录值 |
   |---|---|---|
   | CNAME | `www` | `你的用户名.github.io` |

3. 等 DNS 生效（几分钟到几小时），回到 Pages 设置页勾选 **Enforce HTTPS**

> ⚠️ **重要：绑定自定义域名前，请先完成后文「部署前必做」里的第 1 项**，否则页脚备案号与域名对不上。

---

## 部署前必做：内容核对清单

站点内容全部基于公开工商信息与公司自有资料整理，**以下 4 项请在公开发布前确认**：

### 1. 页脚 ICP 备案与域名必须对应

页脚当前写的是 `闽ICP备15012597号-1`，该备案对应的域名是 **`yiquwl.com`**。

- 如果最终通过 `yiquwl.com` / `www.yiquwl.com` 访问 → ✅ 正确
- 如果暂时只在 `你的用户名.github.io/website/` 访问 → ⚠️ 备案不覆盖 `github.io` 域名，
  建议此时先把页脚的备案号那一行注释掉，绑好域名后再放开

### 2. 联系方式需确认

页面上的电话 `0591-38700218`、邮箱 `nzjiang@qq.com` 来自公开工商信息。请确认：

- [ ] 电话是否仍在使用、是否愿意公开
- [ ] 是否改用公司域名邮箱（如 `contact@yiquwl.com`），比 QQ 邮箱更正式
- [ ] 需要的话补充微信公众号 / 企业微信二维码

### 3. 资质荣誉表述需与实际证书一致

页面上列出的 8 项资质（高新技术企业、科技型中小企业、专精特新中小企业、创新型中小企业、
增值电信业务经营许可证 闽B2-20260993、第二类医疗器械经营备案凭证、纳税信用 A 级、
61 项软件著作权）均有公开记录支撑，但请核对：

- [ ] 证书是否在有效期内
- [ ] 公司对外宣传口径是否允许列出全部项目
- [ ] 61 项软著为检索时点数据，后续如有增减请更新

### 4. 产品描述需业务部门确认

「产品与解决方案」6 个卡片中的产品名称（互联网医院智慧服务管理平台、放射治疗流程管理系统等）
来自公开的软件著作权登记与招投标公告，属真实存在。但**解决方案的介绍文字是概括性描述**，
请业务部门确认表述是否准确，避免对外承诺超出实际交付能力。

> 另：页面**刻意没有写**员工人数、营收数据、客户案例与客户 logo。如果你们希望补充
> 成功案例或客户名录，请提供经确认的材料，我可以加一个「客户案例」区块。

---

## 如何修改内容

### 改文字

所有文案都在 `index.html` 里，用中文写的，直接搜索关键词即可定位。区块顺序：

| 区块 | 在 HTML 中的位置 | 说明 |
|---|---|---|
| 首屏大标题 | `<section class="hero">` | 主标语 + 两句话简介 |
| 关键数据条 | `<section class="stats">` | 4 个数字（2015 / 2000万 / 61项 / A级） |
| 产品与解决方案 | `id="products"` | 6 个卡片，增删卡片直接复制 `<article class="card">` |
| 核心能力 | `id="capability"` | 4 条，编号是手写的 01–04 |
| 资质与荣誉 | `id="honors"` | 8 条，`<span class="honor-badge">` 是左侧小标签 |
| 关于我们 | `id="about"` | 左文右表 |
| 联系我们 | `id="contact"` | 4 个卡片 |
| 页脚 | `<footer class="site-footer">` | 4 栏 + 备案信息 |

页脚版权年份是 JS 自动生成的，不用每年改。

### 换主题色

只改 `assets/css/style.css` 顶部 `:root` 里的三个变量即可，全站生效：

```css
--accent:        #2c55f0;   /* 主色：按钮、图标、强调文字 */
--accent-hover:  #1f41cc;   /* 主色悬停态 */
--accent-soft:   #eef2ff;   /* 主色浅底：图标背景、标签底色 */
```

改完记得同步 `assets/favicon.svg` 里 `<rect>` 的 `fill` 值和 `404.html` 里内联样式中的蓝色，保持一致。

### 加一个新页面

复制 `index.html` 改内容，注意：

- 站内资源路径用**相对路径**（`assets/css/style.css`），不要用 `/assets/...`，
  否则部署在 `用户名.github.io/仓库名/` 子路径下会 404
- 新页面记得在 `sitemap.xml` 里加一条 `<url>`

---

## 技术说明

- **无依赖**：不加载任何外部字体、CSS 框架或 JS 库，首屏无需等待第三方请求
- **字体**：使用系统字体栈（PingFang SC / 微软雅黑 / 思源黑体），中文渲染清晰且零下载
- **响应式**：断点 1024px / 860px / 560px，移动端为汉堡菜单抽屉
- **无障碍**：语义化标签、跳转到主内容链接、可见焦点框、`aria-*` 状态、
  遵循 `prefers-reduced-motion`（用户开启"减弱动效"时关闭全部动画）
- **降级**：禁用 JavaScript 时，`<noscript>` 样式确保所有内容可见；
  脚本若失效，`main.js` 会在 2 秒后退化为滚动监听，内容不会空白
- **SEO**：含 `description`、Open Graph 标签、`canonical`、结构化语义标签
- **打印**：隐藏导航与页脚，卡片避免跨页断开

### 一处需要留意的坑

移动端导航抽屉用 `transform: translateX(100%)` 藏在屏幕右侧之外，
这会让页面产生横向溢出。样式表里用 `html, body { overflow-x: clip; }` 裁掉它 ——
**这里必须用 `clip` 而不是 `hidden`**，因为 `hidden` 会创建滚动容器，
导致顶部导航的 `position: sticky` 失效。

---

## 部署状态

| 项目 | 状态 |
|---|---|
| 本地预览 | ✅ 已验证（1440px / 768px / 390px 三种宽度无横向溢出） |
| HTML 结构 | ✅ 已通过解析器校验，标签闭合完整 |
| 链接完整性 | ✅ 所有锚点、资源路径均已校验 |
| GitHub 仓库 | ⬜ 待创建 |
| Pages 已开启 | ⬜ 待开启 |
| 自定义域名 | ⬜ 待绑定 |
| 内容核对 | ⬜ 见上方「部署前必做」 |
