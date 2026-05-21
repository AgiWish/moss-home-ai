from plugins_func.register import register_function, ToolType, ActionResponse, Action
from plugins_func.functions.hass_init import initialize_hass_handler
from config.logger import setup_logging
import asyncio
import requests
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()


ENTITY_ALIASES = {
    "light.shu_fang_deng": "light.mson_ms006_72e5_light",
    "light.shufang_deng": "light.mson_ms006_72e5_light",
    "light.shufang_light": "light.mson_ms006_72e5_light",
    "light.shufang_zhulight": "light.mson_ms006_72e5_light",
    "light.shufang_main_light": "light.mson_ms006_72e5_light",
    "light.shufang_main": "light.mson_ms006_72e5_light",
    "light.shufang_zhudeng": "light.mson_ms006_72e5_light",
    "switch.shufang_xiaodeng": "switch.iot_tdq3_793a_switch",
    "light.shufang_xiaodeng": "switch.iot_tdq3_793a_switch",
    "switch.shufang_dengdai": "switch.iot_tdq3_793a_switch",
    "light.shufang_dengdai": "switch.iot_tdq3_793a_switch",
    "light.shufang_guadeng": "light.yeelink_lamp22_f8e2_light",
    "light.shufang_hanging_light": "light.yeelink_lamp22_f8e2_light",
    "light.shufang_all": [
        "light.mson_ms006_72e5_light",
        "light.yeelink_lamp22_f8e2_light",
        "switch.iot_tdq3_793a_switch",
    ],
    "light.shu_fang_all": [
        "light.mson_ms006_72e5_light",
        "light.yeelink_lamp22_f8e2_light",
        "switch.iot_tdq3_793a_switch",
    ],
    "switch.ke_ting_xiao_deng": "switch.iot_tdq3_7c10_switch",
    "switch.keting_xiaodeng": "switch.iot_tdq3_7c10_switch",
    "light.ke_ting_qian_deng": "light.mson_ms006_72e9_light",
    "light.ke_ting_hou_deng": "light.mson_ms006_b9c3_light",
    "switch.ke_ting_deng_dai": "switch.iot_tdq3_7adc_switch",
    "light.zhu_wo_deng": "light.mson_ms006_6ef2_light",
    "light.ci_wo_deng": "light.mson_ms006_fa3f_light",
    "light.yang_tai_deng": "light.mson_ms006_6de1_light",
    "cover.shufang": "cover.raex_cura01_c1d1_curtain",
    "cover.shufang_chuanglian": "cover.raex_cura01_c1d1_curtain",
    "cover.shu_fang_chuang_lian": "cover.raex_cura01_c1d1_curtain",
    "cover.zhuwo": "cover.raex_cura01_82c3_curtain",
    "cover.zhuwo_chuanglian": "cover.raex_cura01_82c3_curtain",
    "cover.zhu_wo_chuang_lian": "cover.raex_cura01_82c3_curtain",
    "cover.ciwo": "cover.raex_cura01_8bfe_curtain",
    "cover.ciwo_chuanglian": "cover.raex_cura01_8bfe_curtain",
    "cover.ci_wo_chuang_lian": "cover.raex_cura01_8bfe_curtain",
    "cover.yangtai": "cover.raex_cura01_94dd_curtain",
    "cover.yangtai_chuanglian": "cover.raex_cura01_94dd_curtain",
    "cover.yang_tai_chuang_lian": "cover.raex_cura01_94dd_curtain",
    "vacuum.sao_di_ji": "vacuum.p20_ultra_plus",
    "vacuum.shi_tou": "vacuum.p20_ultra_plus",
    "vacuum.roborock": "vacuum.p20_ultra_plus",
    "climate.shufang": "climate.211106250460304_climate",
    "climate.shufang_kongtiao": "climate.211106250460304_climate",
    "climate.shu_fang_kong_tiao": "climate.211106250460304_climate",
    "climate.keting": "climate.210006738278154_climate",
    "climate.keting_kongtiao": "climate.210006738278154_climate",
    "climate.ke_ting_kong_tiao": "climate.210006738278154_climate",
    "climate.zhuwo": "climate.211106250494646_climate",
    "climate.zhuwo_kongtiao": "climate.211106250494646_climate",
    "climate.zhu_wo_kong_tiao": "climate.211106250494646_climate",
    "climate.ciwo": "climate.208907226270302_climate",
    "climate.ciwo_kongtiao": "climate.208907226270302_climate",
    "climate.ci_wo_kong_tiao": "climate.208907226270302_climate",
    "climate.yangtai": "climate.210006738278640_climate",
    "climate.yangtai_kongtiao": "climate.210006738278640_climate",
    "climate.yang_tai_kong_tiao": "climate.210006738278640_climate",
    "media_player.tv": "media_player.dian_shi",
    "media_player.keting_tv": "media_player.dian_shi",
    "media_player.ke_ting_dian_shi": "media_player.dian_shi",
}


AREA_ALIASES = {
    "客厅": "ke_ting",
    "厨房": "chu_fang",
    "书房": "shu_fang",
    "阳台": "yang_tai",
    "主卧": "zhu_wo",
    "次卧": "ci_wo",
    "卫生间": "wei_sheng_jian",
    "厕所": "wei_sheng_jian",
    "洗手间": "wei_sheng_jian",
    "卧室": "wo_shi",
    "玄关": "xuan_guan",
    "衣帽间": "yi_mao_jian",
}


def resolve_entity_id(entity_id):
    if not entity_id:
        return entity_id
    normalized = entity_id.strip()
    return ENTITY_ALIASES.get(normalized, normalized)


def resolve_area_ids(value):
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = value.replace("，", ",").replace("、", ",").split(",")
    elif isinstance(value, list):
        raw_items = value
    else:
        raw_items = [value]
    area_ids = []
    for item in raw_items:
        key = str(item).strip()
        if not key:
            continue
        area_ids.append(AREA_ALIASES.get(key, key))
    return area_ids


def entity_exists(base_url, api_key, entity_id):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        response = requests.get(
            f"{base_url}/api/states/{entity_id}", headers=headers, timeout=5
        )
    except Exception as exc:
        logger.bind(tag=TAG).warning(f"校验Home Assistant实体失败: {type(exc).__name__}: {exc}")
        return False
    if response.status_code == 200:
        return True
    logger.bind(tag=TAG).warning(
        f"Home Assistant实体不存在: {entity_id}, status:{response.status_code}, body:{response.text[:200]}"
    )
    return False

hass_set_state_function_desc = {
    "type": "function",
    "function": {
        "name": "hass_set_state",
        "description": "设置homeassistant里设备的状态，包括开关、灯光亮度/颜色/色温、播放器音量/暂停/继续，扫地机器人开始/暂停/停止/回充/定位/房间清扫/吸力设置，以及空调制冷/制热/除湿/送风/自动模式和目标温度",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "需要操作的动作,打开设备:turn_on,关闭设备:turn_off,增加亮度:brightness_up,降低亮度:brightness_down,设置亮度:brightness_value,增加音量:volume_up,降低音量:volume_down,设置音量:volume_set,设置色温:set_kelvin,设置颜色:set_color,设备暂停:pause,设备继续:continue,静音/取消静音:volume_mute,扫地机器人回充:return_to_base,扫地机器人定位:locate,扫地机器人局部清扫:clean_spot,扫地机器人房间/区域清扫:clean_area,扫地机器人设置吸力:set_fan_speed,设置空调温度:set_temperature,设置空调模式:set_hvac_mode,设置空调风速:set_fan_mode,设置空调模式和温度:set_climate",
                        },
                        "input": {
                            "type": "integer",
                            "description": "设置音量/亮度时填1-100；设置空调温度set_temperature时填摄氏温度，例如26表示26摄氏度",
                        },
                        "is_muted": {
                            "type": "string",
                            "description": "只有在设置静音操作时才需要,设置静音的时候该值为true,取消静音时该值为false",
                        },
                        "rgb_color": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "只有在设置颜色时需要,这里填目标颜色的rgb值",
                        },
                        "mode": {
                            "type": "string",
                            "description": "空调模式、空调风速或扫地机器人吸力。空调模式可填cool/heat/auto/dry/fan_only/off；用户说制冷填cool，制热填heat，除湿填dry，送风填fan_only，自动填auto；空调风速可填silent/low/medium/high/full/auto；扫地机器人吸力可填quiet/balanced/turbo/max/max_plus/smart_mode/custom；set_climate时这里填空调模式",
                        },
                        "areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "扫地机器人房间/区域清扫时填写Home Assistant区域名或区域id，例如客厅、书房、主卧、次卧、厨房、阳台、卫生间",
                        },
                    },
                    "required": ["type"],
                },
                "entity_id": {
                    "type": "string",
                    "description": "需要操作的设备id,homeassistant里的entity_id",
                },
            },
            "required": ["state", "entity_id"],
        },
    },
}


@register_function("hass_set_state", hass_set_state_function_desc, ToolType.SYSTEM_CTL)
def hass_set_state(conn: "ConnectionHandler", entity_id="", state=None):
    if state is None:
        state = {}
    try:
        ha_response = handle_hass_set_state(conn, entity_id, state)
        return ActionResponse(Action.RESPONSE, ha_response, ha_response)
    except asyncio.TimeoutError:
        logger.bind(tag=TAG).error("设置Home Assistant状态超时")
        return ActionResponse(Action.ERROR, "请求超时", None)
    except Exception as e:
        error_msg = f"执行Home Assistant操作失败"
        logger.bind(tag=TAG).error(error_msg)
        return ActionResponse(Action.ERROR, error_msg, None)


def handle_hass_set_state(conn: "ConnectionHandler", entity_id, state):
    ha_config = initialize_hass_handler(conn)
    api_key = ha_config.get("api_key")
    base_url = ha_config.get("base_url")
    """
    state = { "type":"brightness_up","input":"80","is_muted":"true"}
    """
    entity_id = resolve_entity_id(entity_id)
    if isinstance(entity_id, list):
        results = []
        for item_entity_id in entity_id:
            results.append(handle_hass_set_state(conn, item_entity_id, state))
        if all(("已" in result or "打开" in result or "关闭" in result) for result in results):
            return "已完成"
        return "；".join(results)
    action_type = state.get("type")
    if not action_type:
        return "执行失败，缺少动作类型"
    if not entity_exists(base_url, api_key, entity_id):
        return f"执行失败，找不到设备: {entity_id}"
    domains = entity_id.split(".")
    if len(domains) > 1:
        domain = domains[0]
    else:
        return "执行失败，错误的设备id"
    action = ""
    arg = ""
    value = ""
    if action_type in ("turn_on", "open", "open_cover"):
        description = "设备已打开"
        if domain == "cover":
            action = "open_cover"
        elif domain == "vacuum":
            action = "start"
        else:
            action = "turn_on"
    elif action_type in ("turn_off", "close", "close_cover"):
        description = "设备已关闭"
        if domain == "cover":
            action = "close_cover"
        elif domain == "vacuum":
            action = "stop"
        else:
            action = "turn_off"
    elif action_type in ("stop", "stop_cover"):
        if domain != "cover":
            return "执行失败，停止只能用于窗帘"
        description = "窗帘已停止"
        action = "stop_cover"
    elif action_type == "brightness_up":
        description = "灯光已调亮"
        action = "turn_on"
        arg = "brightness_step_pct"
        value = 10
    elif action_type == "brightness_down":
        description = "灯光已调暗"
        action = "turn_on"
        arg = "brightness_step_pct"
        value = -10
    elif action_type == "brightness_value":
        description = f"亮度已调整到{state['input']}"
        action = "turn_on"
        arg = "brightness_pct"
        value = state["input"]
    elif action_type == "set_color":
        description = f"颜色已调整到{state['rgb_color']}"
        action = "turn_on"
        arg = "rgb_color"
        value = state["rgb_color"]
    elif action_type == "set_kelvin":
        description = f"色温已调整到{state['input']}K"
        action = "turn_on"
        arg = "kelvin"
        value = state["input"]
    elif action_type == "set_temperature":
        description = f"温度已调整到{state['input']}度"
        action = "set_temperature"
        arg = "temperature"
        value = state["input"]
    elif action_type == "set_hvac_mode":
        description = f"空调模式已调整为{state['mode']}"
        action = "set_hvac_mode"
        arg = "hvac_mode"
        value = state["mode"]
    elif action_type == "set_fan_mode":
        description = f"风速已调整为{state['mode']}"
        action = "set_fan_mode"
        arg = "fan_mode"
        value = state["mode"]
    elif action_type == "set_climate":
        if domain != "climate":
            return "执行失败，set_climate 只能用于空调设备"
        temperature = state.get("input")
        hvac_mode = state.get("mode")
        if temperature is None and not hvac_mode:
            return "执行失败，缺少空调模式或温度"
        description = "空调已设置"
        action = "set_temperature"
        arg = "climate_payload"
        value = {"temperature": temperature, "hvac_mode": hvac_mode}
    elif action_type == "volume_up":
        description = "音量已调大"
        action = action_type
    elif action_type == "volume_down":
        description = "音量已调小"
        action = action_type
    elif action_type == "volume_set":
        description = f"音量已调整到{state['input']}"
        action = action_type
        arg = "volume_level"
        value = state["input"]
        if state["input"] >= 1:
            value = state["input"] / 100
    elif action_type == "volume_mute":
        description = f"设备已静音"
        action = action_type
        arg = "is_volume_muted"
        value = state["is_muted"]
        if isinstance(value, str):
            value = value.lower() == "true"
    elif action_type == "pause":
        description = f"设备已暂停"
        action = action_type
        if domain == "media_player":
            action = "media_pause"
        if domain == "cover":
            action = "stop_cover"
        if domain == "vacuum":
            action = "pause"
    elif action_type == "continue":
        description = f"设备已继续"
        if domain == "media_player":
            action = "media_play"
        if domain == "vacuum":
            action = "start"
    elif action_type == "return_to_base":
        if domain != "vacuum":
            return "执行失败，回充只能用于扫地机器人"
        description = "扫地机器人已回充"
        action = "return_to_base"
    elif action_type == "locate":
        if domain != "vacuum":
            return "执行失败，定位只能用于扫地机器人"
        description = "扫地机器人已定位"
        action = "locate"
    elif action_type == "clean_spot":
        if domain != "vacuum":
            return "执行失败，局部清扫只能用于扫地机器人"
        description = "扫地机器人已开始局部清扫"
        action = "clean_spot"
    elif action_type == "clean_area":
        if domain != "vacuum":
            return "执行失败，房间清扫只能用于扫地机器人"
        area_ids = resolve_area_ids(state.get("areas") or state.get("input"))
        if not area_ids:
            return "执行失败，缺少清扫房间"
        description = "扫地机器人已开始清扫指定房间"
        action = "clean_area"
        arg = "cleaning_area_id"
        value = area_ids
    elif action_type == "set_fan_speed":
        if domain != "vacuum":
            return "执行失败，吸力设置只能用于扫地机器人"
        speed = state.get("mode")
        if not speed:
            return "执行失败，缺少吸力档位"
        description = f"扫地机器人吸力已调整为{speed}"
        action = "set_fan_speed"
        arg = "fan_speed"
        value = speed
    else:
        return f"{domain} {action_type}功能尚未支持"

    if arg == "":
        data = {"entity_id": entity_id}
    elif arg == "climate_payload":
        data = {"entity_id": entity_id}
        if value.get("temperature") is not None:
            data["temperature"] = value["temperature"]
        if value.get("hvac_mode"):
            data["hvac_mode"] = value["hvac_mode"]
    else:
        data = {"entity_id": entity_id, arg: value}
    url = f"{base_url}/api/services/{domain}/{action}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=data, timeout=5)  # 设置5秒超时
    logger.bind(tag=TAG).info(
        f"设置状态:{description},url:{url},return_code:{response.status_code}"
    )
    if response.status_code in (200, 201):
        return description
    else:
        logger.bind(tag=TAG).warning(
            f"Home Assistant返回失败: {response.status_code}, body:{response.text[:300]}"
        )
        return f"设置失败，错误码: {response.status_code}"
