# 固件源码与烧录

## 源码位置

原始来源：

```text
/Users/zyh/project/小智AI教程ESP32-S3-N16R8/小智固件与固件源码/小智固件源码/xiaozhi-esp32-main203彩屏固件源码/xiaozhi-esp32-main
```

本项目副本：

```text
firmware/xiaozhi-esp32
```

当前不建议直接在原始下载目录继续改，后续统一在本项目副本里改。

## 硬件

- ESP32-S3-N16R8
- 240 x 320 RGB565 彩屏
- 无摄像头
- 串口：`USB Serial (cu.wchusbserial10)`

## 构建环境

macOS 上使用 ESP-IDF。

常用构建命令：

```bash
cd /Users/zyh/project/AgiWish/moss-home-ai/firmware/xiaozhi-esp32
. /Users/zyh/esp/esp-idf/export.sh
idf.py build
```

烧录：

```bash
idf.py -p /dev/cu.wchusbserial10 flash monitor
```

## UI 方向

当前希望是 MOSS 风格，但不要过度动画导致音频卡顿。

基本状态：

- standby：待机
- listening：正在听
- thinking：正在处理
- speaking：正在说话
- online/offline：连接状态

设计要求：

- 黑底、低亮度、科技感。
- 信息密度适中，不要花哨。
- 动画不能抢 CPU。
- 音频活动时动画降频或简化，避免 I2S buffer underrun。

## 已踩过的坑

### MOSS 主题不是普通 theme 字符串

之前出现过黑屏，原因是 NVS 或代码里设置了不存在的 `moss` theme，但 `lcd_display.cc` 原本只注册 `light` 和 `dark`。

结论：

- 不能只把 theme 名字改成 `moss`。
- 要么注册完整 MOSS 主题。
- 要么在现有 display 逻辑里直接绘制 MOSS UI。
- 必须保证 theme fallback 不会空指针。

### 动画和音频会互相影响

ESP32-S3 上 LVGL 动画、屏幕刷新、I2S 音频共享资源。

要求：

- 说话/播放音频时降低刷新频率。
- 不用大 GIF。
- 不做全屏高频粒子动画。
- 交互优先稳定。

