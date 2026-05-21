# 当前状态快照

更新时间：2026-05-21

## 当前目标

把家里的小智设备做成一个可长期迭代的本地家庭 AI 中控：

- 设备端有 MOSS 风格 UI。
- 后端连接 NAS 自部署小智服务。
- 可以通过 Home Assistant 控制家里设备。
- 可以通过 Music Assistant 播放音乐到 Apple TV / 索尼电视。
- 后续可以继续扩展成更稳定的语音家庭管家。

## 当前设备

- 设备：ESP32-S3-N16R8
- 屏幕：240 x 320，RGB565
- 串口：`USB Serial (cu.wchusbserial10)`
- 固件源码来源：
  `/Users/zyh/project/小智AI教程ESP32-S3-N16R8/小智固件与固件源码/小智固件源码/xiaozhi-esp32-main203彩屏固件源码/xiaozhi-esp32-main`
- 本项目内副本：
  `firmware/xiaozhi-esp32`

## 当前 NAS 后端

- NAS：`<NAS_IP>`
- SSH：`ssh -p <SSH_PORT> root@<NAS_IP>`
- 小智后端目录：`/volume1/docker/xiaozhi-server`
- 小智后端容器：
  - `xiaozhi-esp32-server`
  - `xiaozhi-esp32-server-web`
  - `xiaozhi-esp32-server-db`
  - `xiaozhi-esp32-server-redis`
- Home Assistant 容器：`homeassistant`
- Music Assistant 容器：`music-assistant`

## 当前小智智能体

- Agent ID：`e7f9852050a44bc293f51bf88d1863e0`
- 名称：小智
- 当前 LLM：`LLM_AliLLM`
- 当前模型配置方向：语音控制优先快响应，使用短输出。
- 当前 ASR：`ASR_Qwen3Flash`
- 当前 TTS：`TTS_EdgeTTS`
- 当前语音：`zh-CN-YunyangNeural`

## 已完成修复

- 唤醒回复不再使用台湾腔女声，改为男声“我在”。
- Home Assistant 控制规则已经补充灯、窗帘、空调、扫地机器人、电视。
- 窗帘控制已支持 `open/close/stop/turn_on/turn_off`。
- “嗯/这个/那个”等短句不再反复要求“请说完整指令”。
- Music Assistant 默认 Apple TV 播放目标可用。
- Apple TV 音乐播放音量低的问题已加最低音量保护：低于 55 自动拉到 55。

## 当前还需要继续优化

- 语音识别偶尔听不全，仍可能提前截断。
- 复杂对话和家庭控制混在一起时，模型可能误判意图。
- Apple TV / SenPlayer 目前只能遥控级控制，不能直接按剧名播放。
- 音乐搜索和缓存链路可用性需要继续验证。
- 固件 UI 已经过多轮修改，但还需要把最终设计系统稳定下来。

