# 下一步计划

## 优先级 P0

### 1. 固件源码统一

- 后续只改 `firmware/xiaozhi-esp32`。
- 不再改下载目录里的原始源码。
- 确认当前可成功 build + flash。
- 把当前可用固件 tag 成一个 baseline。

### 2. 小智后端补丁同步

NAS 上真实运行补丁：

```text
/volume1/docker/xiaozhi-server/patches/hass_set_state.py
/volume1/docker/xiaozhi-server/patches/hass_play_music.py
```

本项目副本：

```text
backend-patches/hass_set_state.py
backend-patches/hass_play_music.py
```

以后改逻辑时：

1. 先在本项目改。
2. 再同步到 NAS patches。
3. 重启 `xiaozhi-esp32-server`。
4. 语音实测。

### 3. Apple TV 遥控器动作

给 `hass_set_state.py` 补：

- `remote_up`
- `remote_down`
- `remote_left`
- `remote_right`
- `remote_select`
- `remote_back`
- `remote_home`

这样小智可以控制 SenPlayer 当前界面。

## 优先级 P1

### 4. 音乐搜索链路验证

测试：

- “播放音乐”
- “换一首”
- “播放周杰伦”
- “播放某首歌”
- 115 资源命中后是否能缓存并播放

### 5. 语音识别稳定性

继续看：

- VAD 是否过早截断。
- ASR 是否把短句误识别。
- 说话时音频是否卡顿。

### 6. UI 稳定化

目标：

- 好看，但不抢 CPU。
- 不再频繁返工动画。
- MOSS 视觉统一成一个明确组件体系。

## 优先级 P2

### 7. 精准播放影视

如果要说“播放某部电视剧第几集”，不要优先走 SenPlayer。

更靠谱路径：

- Emby/Jellyfin 媒体库 API
- 查片名、季、集
- 返回播放 URL
- 推到 Apple TV / Infuse / 电视

### 8. 家庭场景

可做：

- 睡觉模式
- 起床模式
- 观影模式
- 回家模式
- 离家模式
- 专注模式
- 夜间走动模式

重点是不要影响家里其他人。

