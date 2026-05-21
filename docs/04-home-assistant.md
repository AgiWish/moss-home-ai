# Home Assistant 控制逻辑

## HA 地址

```text
http://192.168.5.8:8123
```

## 当前实体映射

### 灯

```text
客厅前灯 light.mson_ms006_72e9_light
客厅后灯 light.mson_ms006_b9c3_light
客厅灯带 switch.iot_tdq3_7adc_switch
客厅小灯 switch.iot_tdq3_7c10_switch

书房灯 light.mson_ms006_72e5_light
书房挂灯 light.yeelink_lamp22_f8e2_light
书房小灯 switch.iot_tdq3_793a_switch

主卧灯 light.mson_ms006_6ef2_light
主卧小灯 switch.iot_tdq3_7b8a_switch

次卧灯 light.mson_ms006_fa3f_light
次卧小灯 switch.iot_tdq3_7c26_switch

阳台灯 light.mson_ms006_6de1_light
阳台小灯 switch.iot_tdq3_7ba1_switch
```

### 窗帘

```text
书房窗帘 cover.raex_cura01_c1d1_curtain
主卧窗帘 cover.raex_cura01_82c3_curtain
次卧窗帘 cover.raex_cura01_8bfe_curtain
阳台窗帘 cover.raex_cura01_94dd_curtain
```

支持动作：

```text
turn_on/open/open_cover    -> open_cover
turn_off/close/close_cover -> close_cover
pause/stop/stop_cover      -> stop_cover
```

### 空调

```text
主卧空调 climate.211106250494646_climate
客厅空调 climate.210006738278154_climate
阳台空调 climate.210006738278640_climate
次卧空调 climate.208907226270302_climate
书房空调 climate.211106250460304_climate
```

支持：

- 开关
- 制冷：`cool`
- 制热：`heat`
- 除湿：`dry`
- 送风：`fan_only`
- 自动：`auto`
- 设置温度
- 一次性设置模式 + 温度：`set_climate`

### 扫地机器人

```text
vacuum.p20_ultra_plus
```

支持：

- 开始清扫
- 暂停
- 停止
- 回充
- 定位
- 按房间清扫
- 吸力模式

已知房间名：

```text
客厅、书房、主卧、次卧、厨房、阳台、卫生间
```

### 电视 / Apple TV

```text
media_player.dian_shi       # Apple TV / 客厅电视 HA 实体
media_player.dian_shi_2     # Music Assistant 暴露的 Apple TV 播放队列
remote.dian_shi             # Apple TV 遥控器
```

当前能做：

- 打开电视
- 关闭电视
- 播放
- 暂停
- 继续
- 遥控器方向键和确认键需要后续补工具

不能天然做：

- 直接在 SenPlayer 里按剧名搜索并播放某一集。

## 语音控制原则

- 明确设备 + 明确动作，才执行。
- 工具成功后才说“好了”。
- 短句如“嗯/这个/那个”不要反复追问完整指令。
- 不确定客厅哪盏灯时，先问“要控制客厅哪盏灯”。

