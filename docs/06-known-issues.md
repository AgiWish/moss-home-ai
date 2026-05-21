# 已知问题与处理记录

## 1. 窗帘打开失败

现象：

```text
cover open功能尚未支持
```

原因：

- 模型调用 `state.type=open`。
- 原 `hass_set_state.py` 只支持 `turn_on/turn_off`。

处理：

- 已支持 `open/close/stop/open_cover/close_cover/stop_cover`。

## 2. “请说完整指令”反复出现

现象：

- 用户正常说“嗯”“这个”等短句时，小智一直回复“请说完整指令”。

原因：

- Prompt 规则太硬，把所有短句都要求澄清。

处理：

- 改为短句无明确动作时安静等待，最多说“请说”。

## 3. Apple TV 音乐声音小

现象：

- 电视音量调高，但音乐依然小。

原因：

- Music Assistant 里的 Apple TV player 音量是 20。
- 电视物理音量和 MA/AirPlay 音量不是同一个控制层。

处理：

- 已加 `TV_MIN_MUSIC_VOLUME = 55`。

## 4. 台湾腔女声

现象：

- 唤醒时出现女性“我在这里哦”，进入对话后又是男声。

原因：

- 唤醒音频 fallback 到内置女性短音频。
- 自定义音频文件太小，被小智后端判定无效。

处理：

- 生成 `wakeup_yunyang_wozai_padded.wav`。
- `.wakeup_words.yaml` 指向该文件。

## 5. MOSS UI 黑屏

现象：

- 烧录后黑屏或白屏。

可能原因：

- 设置了不存在的 theme 名称。
- LVGL 对象生命周期错误。
- 当前硬件屏幕驱动不匹配。
- 动画负载太高。

处理方向：

- 不直接设置不存在的 `moss` theme。
- 在当前屏幕驱动和 board 配置基础上做 UI。
- 音频状态下降低动画负载。

## 6. SenPlayer 无法按剧名播放

原因：

- HA 只能遥控 Apple TV。
- SenPlayer 内部媒体库不可见。

处理方向：

- 短期做遥控器宏。
- 长期接 Emby/Jellyfin/Infuse 可查询媒体库的方案。

