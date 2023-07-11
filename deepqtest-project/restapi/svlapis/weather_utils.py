# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/15 16:57
# @Author  : Chengjie
# @File    : weather_utils.py
import json


def map_real_to_virtual(time_stamp, real_weather):
    weather_Map = open('./openweather-database/Weather_Map.json', 'r')
    content = weather_Map.read()
    wea_map = json.loads(s=content)

    fixed = True

    day_weather = real_weather[time_stamp]

    humidity = day_weather['main']['humidity']
    clouds = day_weather['clouds']['all']
    wea_id = day_weather['weather'][0]['id']

    rain_level = 0
    fog_level = 0
    wetness_level = humidity / 100
    cloudiness_level = clouds / 100

    if wea_id < 300:
        """
        Main: Thunderstorm
        """
        rain_level = wea_map[str(wea_id)]['Virtual_Description']
    elif 300 <= wea_id < 400:
        """
        Main: Drizzle
        """
        rain_level = wea_map[str(wea_id)]['Virtual_Description']
        if wea_id in [313, 314, 321]:
            fixed = False
    elif 500 <= wea_id < 600:
        """
        Main: Rain
        """
        rain_level = wea_map[str(wea_id)]['Virtual_Description']
        if wea_id in [520, 521, 522, 531]:
            fixed = False
    elif 700 <= wea_id < 800:
        fog_level = wea_map[str(wea_id)]['Virtual_Description']

    elif wea_id == 800:
        rain_level = 0
        fog_level = 0

    elif 800 < wea_id < 810:
        """
        Cloud level depend on 'clouds'.
        """
        pass

    print('rain_level: {}, fog_level: {}, wetness_level: {}, cloudiness_level: {}, fixed: {}'.
          format(rain_level, fog_level, wetness_level, cloudiness_level, fixed))
    return rain_level, fog_level, wetness_level, cloudiness_level, fixed
