# MOSS UI 审查

更新时间：2026-05-21

## 结论

MOSS 相关内容已经进入项目文档，但当前固件源码里还没有完整、独立的 MOSS UI 实现。

当前状态可以理解为：

```text
MOSS 方向 / 设计目标 / 踩坑记录：已放入项目
MOSS 固件源码完整实现：未完成
当前可编译固件源码副本：已放入项目
```

## 已放进去的 MOSS 内容

### 文档层

这些文件已经明确记录 MOSS 方向：

```text
README.md
docs/00-current-state.md
docs/01-architecture.md
docs/02-firmware.md
docs/06-known-issues.md
docs/07-next-steps.md
```

已记录的信息包括：

- 设备端目标是 MOSS 风格 UI。
- 当前设备是 ESP32-S3-N16R8 + 240x320 RGB565 彩屏。
- 不要回到默认云端视觉。
- MOSS UI 要黑底、科技感、低动画负载。
- 音频活动时不能用高频动画抢 CPU。
- 之前黑屏和 `theme=moss` 相关。

### 固件源码层

当前小智固件源码已经同步到：

```text
firmware/xiaozhi-esp32
```

这是后续实现 MOSS UI 的主代码库。

## 当前源码里还没有的内容

### 1. 没有 `moss` theme 注册

当前 `firmware/xiaozhi-esp32/main/display/lcd_display.cc` 只注册了：

```cpp
theme_manager.RegisterTheme("light", light_theme);
theme_manager.RegisterTheme("dark", dark_theme);
```

没有：

```cpp
theme_manager.RegisterTheme("moss", moss_theme);
```

所以不能直接把屏幕 theme 设置成 `moss`。

### 2. MCP 设备工具也只暴露 light/dark

当前 `firmware/xiaozhi-esp32/main/mcp_server.cc` 里 `self.screen.set_theme` 的描述仍是：

```text
The theme can be `light` or `dark`.
```

这说明设备端控制协议还没有正式把 `moss` 作为可选主题暴露出去。

### 3. 没有独立 MOSS 显示组件

当前没有找到这些类型的文件：

```text
moss_display.cc
moss_display.h
moss_theme.cc
moss_theme.h
moss_face.cc
moss_status_view.cc
```

目前仍然是原小智的 `LcdDisplay` / `EmoteDisplay` / board display 逻辑。

### 4. 当前显示状态还是原小智状态映射

例如 `firmware/xiaozhi-esp32/main/display/emote_display.cc` 仍按原状态处理：

```cpp
LISTENING -> SHOW_LISTENING
STANDBY   -> SHOW_TIME
SPEAKING  -> SHOW_TIPS
ERROR     -> SHOW_TIPS
```

还没有替换成真正的 MOSS 状态面板：

```text
MOSS ONLINE
STANDBY
LISTENING
PROCESSING
SPEAKING
```

## 之前为什么屏幕上能看到 MOSS ONLINE

可能原因有两个，需要后续通过 git diff 或烧录固件反查确认：

1. 之前某次修改是在原始下载目录完成的，没有被完整同步到当前 `moss-home-ai/firmware/xiaozhi-esp32`。
2. 之前显示的 “MOSS ONLINE” 是临时实验代码或烧录产物，而不是现在这个源码副本里的稳定实现。

当前仓库内不能证明完整 MOSS UI 已经落地。

## 下次实现 MOSS UI 的建议

不要直接设置 `theme=moss`，应该走更稳的三步：

### 第一步：加安全 fallback

在 `lcd_display.cc` 里读取 theme 后，如果 `GetTheme(theme_name)` 返回空，必须 fallback 到 `dark` 或 `light`。

避免再黑屏：

```cpp
current_theme_ = LvglThemeManager::GetInstance().GetTheme(theme_name);
if (current_theme_ == nullptr) {
    current_theme_ = LvglThemeManager::GetInstance().GetTheme("dark");
}
```

### 第二步：先注册 MOSS 色彩主题

在 `InitializeLcdThemes()` 里注册 `moss`，但仍复用现有布局。

目标：

- 黑底
- 青色主色
- 低亮文本
- 不改复杂布局

### 第三步：再做 MOSS 状态面板

等主题稳定后，再改布局：

- 顶部：`MOSS ONLINE`
- 中部：圆形核心 / 状态文字
- 底部：连接状态 / 音频状态
- 监听、思考、说话时只做轻量动画

## 下一步验收标准

真正算 MOSS 内容落地，需要满足：

- `rg "RegisterTheme\\(\"moss\"" firmware/xiaozhi-esp32/main` 能搜到。
- `self.screen.set_theme` 支持 `moss`，或者设备默认就是 MOSS UI。
- 固件烧录后稳定显示 MOSS 状态，不黑屏。
- 对话时音频不卡顿。
- 文档里记录了修改文件和烧录命令。

