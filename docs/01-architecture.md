# 整体架构

## 总链路

```text
用户语音
  ↓
ESP32-S3 小智设备
  - 麦克风采集
  - 唤醒词
  - WebSocket 连接后端
  - MOSS 风格屏幕 UI
  ↓
NAS 小智后端
  - ASR
  - LLM
  - TTS
  - 工具调用
  ↓
Home Assistant / Music Assistant
  - 灯
  - 窗帘
  - 空调
  - 扫地机器人
  - Apple TV / 索尼电视
  - 音乐播放
```

## 后端服务分工

小智后端：

- 负责设备连接、语音转文字、模型调用、TTS、插件工具。
- 家庭控制通过 `hass_set_state.py`。
- 音乐播放通过 `hass_play_music.py`。

Home Assistant：

- 负责真实设备控制。
- 小米、米家、美的、石头、Apple TV、Sony TV 等设备统一暴露为实体。

Music Assistant：

- 负责音乐库和播放器。
- 默认输出到 Apple TV / 索尼电视。
- 后续接 115 音乐资源缓存。

Apple TV / Sony TV：

- Apple TV 是 AirPlay 播放目标。
- Sony TV 是实际外放设备。
- SenPlayer 当前只能通过遥控器级别控制，不能天然按剧名精准播放。

## 设计原则

- 小智设备优先短响应，不做长篇聊天。
- 家庭控制必须先调用工具，工具成功后才能回答“好了”。
- 不确定设备时先问，不随机控制。
- 语音设备以稳定为先，不追求复杂人格。
- 不把 token、API key、密码写入仓库。

