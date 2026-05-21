# NAS 小智后端

## SSH

```bash
ssh -p 223 root@192.168.5.8
```

进入后先设置 Docker PATH：

```bash
export PATH=/usr/local/bin:/var/packages/ContainerManager/target/usr/bin:/volume1/@appstore/ContainerManager/usr/bin:$PATH
```

## 目录

```text
/volume1/docker/xiaozhi-server
```

关键文件：

```text
/volume1/docker/xiaozhi-server/patches/hass_set_state.py
/volume1/docker/xiaozhi-server/patches/hass_play_music.py
/volume1/docker/xiaozhi-server/data/.wakeup_words.yaml
/volume1/docker/xiaozhi-server/data/wakeup_yunyang_wozai_padded.wav
```

这些 patch 通过 Docker volume 挂进容器：

```text
/volume1/docker/xiaozhi-server/patches/hass_set_state.py
  -> /opt/xiaozhi-esp32-server/plugins_func/functions/hass_set_state.py

/volume1/docker/xiaozhi-server/patches/hass_play_music.py
  -> /opt/xiaozhi-esp32-server/plugins_func/functions/hass_play_music.py
```

## 容器

```text
xiaozhi-esp32-server
xiaozhi-esp32-server-web
xiaozhi-esp32-server-db
xiaozhi-esp32-server-redis
homeassistant
music-assistant
```

查看：

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

重启小智后端：

```bash
cd /volume1/docker/xiaozhi-server
docker compose restart xiaozhi-esp32-server
```

## 日志

看语音识别、模型、工具调用：

```bash
docker logs --since=20m xiaozhi-esp32-server 2>&1 \
  | grep -E '识别文本|大模型收到|执行工具|hass_set_state|hass_play_music|失败|返回|播放音乐'
```

看 Home Assistant：

```bash
docker logs --since=20m homeassistant 2>&1 \
  | grep -Ei 'error|failed|service|apple_tv|midea|xiaomi|cover|light|vacuum'
```

看 Music Assistant：

```bash
docker logs --since=20m music-assistant 2>&1 \
  | grep -Ei 'apfeb2842e85f8|电视|AirPlay|volume|play|stream|error|failed'
```

## 数据库

数据库容器：`xiaozhi-esp32-server-db`

```bash
docker exec xiaozhi-esp32-server-db mysql --default-character-set=utf8mb4 -uroot -p123456 xiaozhi_esp32_server
```

当前 Agent：

```text
e7f9852050a44bc293f51bf88d1863e0
```

常查表：

```sql
SELECT id,agent_name,llm_model_id,slm_model_id,asr_model_id,vad_model_id,tts_model_id,tts_voice_id
FROM ai_agent
WHERE id='e7f9852050a44bc293f51bf88d1863e0';

SELECT id,model_type,model_code,config_json
FROM ai_model_config
WHERE id IN ('LLM_AliLLM','ASR_Qwen3Flash','VAD_SileroVAD');
```

## 当前关键后端逻辑

### `hass_set_state.py`

负责 HA 设备控制：

- 灯：`turn_on/turn_off/brightness`
- 窗帘：`open/close/stop/turn_on/turn_off`
- 空调：开关、温度、模式、组合设置
- 扫地机器人：开始、暂停、停止、回充、定位、区域清扫、吸力
- 电视：开关、播放、暂停、继续

### `hass_play_music.py`

负责音乐：

- 默认 Apple TV / 索尼电视播放。
- Apple TV MA player id：`apfeb2842e85f8`
- 备用乐播 AirPlay。
- 最后 fallback 到小爱音箱。
- 从 MA 库找歌，找不到再尝试 115 资源缓存。
- 电视播放前会检查 MA 音量，低于 55 自动拉到 55。
- 不再自动调小爱音箱音量或静音状态。

