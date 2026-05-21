# Backend Patches

这里保存 NAS 小智后端关键插件的脱敏副本。

真实运行位置：

```text
/volume1/docker/xiaozhi-server/patches/
```

Docker 挂载位置：

```text
/opt/xiaozhi-esp32-server/plugins_func/functions/
```

注意：

- 不要在仓库里提交真实 API key、HA token、Music Assistant 密码。
- 本目录里的 `hass_play_music.py` 已将 MA 账号密码替换为占位符。
- 如果要部署到 NAS，需要把真实配置放回 NAS 环境或由配置文件读取。

