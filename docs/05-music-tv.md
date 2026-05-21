# 音乐、电视、Apple TV、SenPlayer

## Music Assistant

地址：

```text
http://192.168.5.8:8096
```

当前主要播放器：

```text
Apple TV / 电视
player_id: apfeb2842e85f8
```

其他历史目标：

```text
乐播投屏 AirPlay: ap56d0040bdeb3
乐播 DLNA/Universal: up7b227e0ddfbe2b27f5d07c22df10ea3a
客厅小黑: media_player.xiaomi_oh2p_1813_play_control
```

## 当前播放策略

默认：

```text
小智，播放音乐
  -> hass_play_music
  -> media_player.dian_shi_2
  -> PLAYER_ALIASES
  -> apfeb2842e85f8
  -> Music Assistant
  -> Apple TV AirPlay
  -> 索尼电视出声
```

fallback：

```text
Apple TV 不可用
  -> 乐播 AirPlay
  -> 小爱音箱
```

## 音量问题处理

出现过的问题：

- 电视音量调大了，但音乐还是很小。

真实原因：

- HA 电视实体音量不是 AirPlay 播放队列音量。
- Music Assistant 里的 Apple TV 播放器音量只有 20。

已处理：

- `hass_play_music.py` 增加 `TV_MIN_MUSIC_VOLUME = 55`
- 播放到电视目标前：
  - 读取 MA player 音量
  - 如果低于 55，自动调用 `players/cmd/volume_set`
  - 小爱音箱不做这个处理

## 115 音乐资源

当前方向：

- 不把 7T 资源全量复制到本地。
- 115 挂载作为资源库。
- 小智搜歌时：
  - 先查 Music Assistant 库
  - 查不到再扫 `/music_resource`
  - 命中后复制单曲到 `/music_library/115缓存`
  - 触发音乐库扫描
  - 再播放

容器内路径：

```text
/music_resource
/music_library/115缓存
```

NAS 挂载来源：

```text
/volume1/CloudNAS/CloudDrive/115/音乐/资源库
/volume1/docker/music/library
```

## Apple TV / SenPlayer

当前 HA 能看到 Apple TV：

```text
media_player.dian_shi
remote.dian_shi
```

能做：

- 播放 / 暂停 / 继续
- 打开 / 关闭
- 通过 remote 发送按键，后续可补

不能稳定做：

- 直接说“播放某电视剧某一集”，然后控制 SenPlayer 搜索并播放。

原因：

- SenPlayer 没有被 HA 暴露出媒体库 API。
- Apple TV 集成只能知道当前 app 和播放状态，不等于能操作 SenPlayer 内部搜索。

后续可做：

- 给 `hass_set_state.py` 增加 Apple TV remote 工具动作：
  - up/down/left/right/select/back/home/menu
  - next/previous
- 做固定宏：打开 SenPlayer、继续播放、下一集。
- 如果要按剧名精准播放，建议接 Emby/Jellyfin API，而不是依赖 SenPlayer。

