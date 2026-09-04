# 910×1236 版式规范

## 画布与网格

| 项目 | 固定值 |
|---|---:|
| 画布 | 910 × 1236 px |
| 主内容左边 | 86 px |
| 主内容宽 | 754 px |
| 两栏间距 | 38 px |
| 单栏宽 | 358 px |
| 模块基础圆角 | 9 px |
| 品牌主绿 | `#08B89C` |
| 价值绿 | `#00A95B` |
| 标题黑 | `#222123` |
| 正文灰 | `#3F4545` |

## 字体令牌

| 层级 | 字体 | 字号 | 字重 | 行高 | 字间距 |
|---|---|---:|---:|---:|---:|
| 主标题 | MiSans Heavy | 64 px | 900 | 0.98 | -2.2 px |
| 副标题 | MiSans Regular | 28 px | 400 | 1.18 | -0.6 px |
| 章节标题 | MiSans Medium | 28 px | 500 | 1.15 | -0.4 px |
| 客户简介正文 | MiSans Regular | 16 px | 400 | 1.58 | 0 px |
| 痛点卡标题 | MiSans Semibold | 17 px | 600 | 1.2 | 0.2 px |
| 痛点卡正文 | MiSans Regular | 14.5 px | 400 | 1.48 | 0 px |
| 价值卡标题 | MiSans Semibold | 17 px | 600 | 1.24 | 0 px |
| 价值卡正文 | MiSans Regular | 14.5 px | 400 | 1.48 | 0 px |
| 图片标注 | MiSans Medium | 10 px | 500 | 1 | 0.4 px |

## 垂直定位

| 模块 | 位置/高度 |
|---|---:|
| Logo | `left:64px; top:45px; width:142px` |
| 主标题 | `left:84px; top:135px` |
| 副标题 | `left:85px; top:235px` |
| 客户简介 | `left:86px; top:286px; width:754px; height:126px` |
| 需求痛点标题 | `top:434px` |
| 痛点网格 | `top:475px; height:246px` |
| 方案及价值标题 | `top:747px` |
| 价值网格 | `top:793px; height:357px` |
| 底部波浪 | `top:1148px` 开始，不得遮住卡片 |

## 稳定性规则

- 顶部背景只能使用 `assets/hero-background.png`，文件 SHA-256 必须为 `e8a003bb9f237df04addfc5f45df376e254bb95d49bfed9e65217a36458b3487`。未经用户明确要求，不重新生成、替换、调色、裁切或覆盖。
- 所有定位使用 px，不使用视口百分比或自适应重排。
- 产品截图容器固定宽高，使用 `object-fit: cover`；对重要字段裁切不当时调整 `object-position`，不拉伸图片。
- 页面导出前必须等待字体加载完成：`await document.fonts.ready`。
- 只有用户明确要求新规格时才修改本文件与 `assets/template.html`。
