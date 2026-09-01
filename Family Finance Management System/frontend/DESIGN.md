# Family Finance Management System Design

## Theme

这是一个采用克制专业风格的家庭收支产品界面。白色内容区让账目和表格易于扫描，深橄榄色用于主导航与关键操作，柔和的青绿、琥珀和珊瑚分别表达健康、提醒和超支状态。

## Color

```css
:root {
  --ff-bg: oklch(0.975 0.008 135);
  --ff-surface: oklch(1 0 0);
  --ff-panel: oklch(0.952 0.014 140);
  --ff-ink: oklch(0.25 0.035 145);
  --ff-muted: oklch(0.48 0.025 145);
  --ff-primary: oklch(0.38 0.075 135);
  --ff-income: oklch(0.52 0.105 150);
  --ff-warning: oklch(0.7 0.13 76);
  --ff-expense: oklch(0.59 0.16 28);
}
```

## Typography

使用系统无衬线字体。页面标题为 24px/600，区块标题为 16px/600，数据表和表单维持 14px 的紧凑密度；金额使用等宽数字特性。

## Layout

桌面端使用 232px 深色侧栏、64px 顶栏和可滚动的内容区。内容最大宽度为 1440px，仪表盘采用响应式网格，窄屏时侧栏收起并让表格横向滚动。

## Components

Ant Design 提供 Menu、Table、Form、Drawer、Statistic、Progress、Tag、Alert 与日期控件。页面容器不再额外嵌套卡片；仅摘要、图表和编辑区使用低圆角表面。
