# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/11 10:20
# @Author  : Chengjie
# @File    : weather_map.py
import json

weather_map = {
    "200": {
        "Main": "Thunderstorm",
        "Real_Description": "thunderstorm with light rain",
        "Virtual_Description": "0.3"
    },
    "201": {
        "Main": "Thunderstorm",
        "Real_Description": "thunderstorm with rain",
        "Virtual_Description": "0.6"
    },
    "202": {
        "Main": "Thunderstorm",
        "Real_Description": "thunderstorm with heavy rain",
        "Virtual_Description": "0.9"
    },
    "210": {
        "Main": "Thunderstorm",
        "Real_Description": "light thunderstorm",
        "Virtual_Description": "0.2"
    },
    "211": {
        "Main": "Thunderstorm",
        "Real_Description": "thunderstorm",
        "Virtual_Description": "0.4"
    },
    "212": {
        "Main": "Thunderstorm",
        "Real_Description": "heavy thunderstorm",
        "Virtual_Description": "0.6"
    },
    "221": {
        "Main": "Thunderstorm",
        "Real_Description": "ragged thunderstorm",
        "Virtual_Description": "0.8"
    },
    "230": {
        "Main": "Thunderstorm",
        "Real_Description": "thunderstorm with light drizzle",
        "Virtual_Description": ""
    },
    "231": {
        "Main": "Thunderstorm",
        "Real_Description": "thunderstorm with drizzle",
        "Virtual_Description": ""
    },
    "232": {
        "Main": "Thunderstorm",
        "Real_Description": "thunderstorm with heavy drizzle",
        "Virtual_Description": ""
    },

    # Drizzle

    "300": {
        "Main": "Drizzle",
        "Real_Description": "light intensity drizzle",
        "Virtual_Description": ""
    },
    "301": {
        "Main": "Drizzle",
        "Real_Description": "drizzle",
        "Virtual_Description": ""
    },
    "302": {
        "Main": "Drizzle",
        "Real_Description": "heavy intensity drizzle",
        "Virtual_Description": ""
    },
    "310": {
        "Main": "Drizzle",
        "Real_Description": "light intensity drizzle rain",
        "Virtual_Description": ""
    },
    "311": {
        "Main": "Drizzle",
        "Real_Description": "drizzle rain",
        "Virtual_Description": ""
    },
    "312": {
        "Main": "Drizzle",
        "Real_Description": "heavy intensity drizzle rain",
        "Virtual_Description": ""
    },
    "313": {
        "Main": "Drizzle",
        "Real_Description": "shower rain and drizzle",
        "Virtual_Description": ""
    },
    "314": {
        "Main": "Drizzle",
        "Real_Description": "heavy shower rain and drizzle",
        "Virtual_Description": ""
    },
    "321": {
        "Main": "Drizzle",
        "Real_Description": "shower drizzle",
        "Virtual_Description": ""
    },

    # Rain
    "500": {
        "Main": "Rain",
        "Real_Description": "light rain",
        "Virtual_Description": "0.2"
    },
    "501": {
        "Main": "Rain",
        "Real_Description": "moderate rain",
        "Virtual_Description": "0.4"
    },
    "502": {
        "Main": "Rain",
        "Real_Description": "heavy intensity rain",
        "Virtual_Description": "0.6"
    },
    "503": {
        "Main": "Rain",
        "Real_Description": "very heavy rain",
        "Virtual_Description": "0.8"
    },
    "504": {
        "Main": "Rain",
        "Real_Description": "extreme rain",
        "Virtual_Description": "1"
    },
    "511": {
        "Main": "Rain",
        "Real_Description": "freezing rain",
        "Virtual_Description": "0.2"
    },
    "520": {
        "Main": "Rain",
        "Real_Description": "light intensity shower rain",
        "Virtual_Description": "0.4"
    },
    "521": {
        "Main": "Rain",
        "Real_Description": "shower rain",
        "Virtual_Description": "0.6"
    },
    "522": {
        "Main": "Rain",
        "Real_Description": "heavy intensity shower rain",
        "Virtual_Description": "0.8"
    },
    "531": {
        "Main": "Rain",
        "Real_Description": "ragged shower rain",
        "Virtual_Description": "1"
    },

    # Snow
    "600": {
        "Main": "Snow",
        "Real_Description": "light snow",
        "Virtual_Description": ""
    },
    "601": {
        "Main": "Snow",
        "Real_Description": "Snow",
        "Virtual_Description": ""
    },
    "602": {
        "Main": "Snow",
        "Real_Description": "Heavy snow",
        "Virtual_Description": ""
    },
    "611": {
        "Main": "Snow",
        "Real_Description": "Sleet",
        "Virtual_Description": ""
    },
    "612": {
        "Main": "Snow",
        "Real_Description": "Light shower sleet",
        "Virtual_Description": ""
    },
    "613": {
        "Main": "Snow",
        "Real_Description": "Shower sleet",
        "Virtual_Description": ""
    },
    "615": {
        "Main": "Snow",
        "Real_Description": "Light rain and snow",
        "Virtual_Description": ""
    },
    "616": {
        "Main": "Snow",
        "Real_Description": "Rain and snow",
        "Virtual_Description": ""
    },
    "620": {
        "Main": "Snow",
        "Real_Description": "Light shower snow",
        "Virtual_Description": ""
    },
    "621": {
        "Main": "Snow",
        "Real_Description": "Shower snow",
        "Virtual_Description": ""
    },
    "622": {
        "Main": "Snow",
        "Real_Description": "Heavy shower snow",
        "Virtual_Description": ""
    },

    # Atmosphere
    "701": {
        "Main": "Mist",
        "Real_Description": "mist",
        "Virtual_Description": "0.2"
    },
    "711": {
        "Main": "Smoke",
        "Real_Description": "Smoke",
        "Virtual_Description": "0.3"
    },
    "721": {
        "Main": "Haze",
        "Real_Description": "Haze",
        "Virtual_Description": "0.4"
    },
    "731": {
        "Main": "Dust",
        "Real_Description": "sand/ dust whirls",
        "Virtual_Description": "0.5"
    },
    "741": {
        "Main": "Fog",
        "Real_Description": "fog",
        "Virtual_Description": "0.6"
    },
    "751": {
        "Main": "Sand",
        "Real_Description": "sand",
        "Virtual_Description": "0.7"
    },
    "761": {
        "Main": "Dust",
        "Real_Description": "dust",
        "Virtual_Description": "0.8"
    },
    "762": {
        "Main": "Ash",
        "Real_Description": "volcanic ash",
        "Virtual_Description": "0.9"
    },
    "771": {
        "Main": "Squall",
        "Real_Description": "squalls",
        "Virtual_Description": "1"
    },
    "781": {
        "Main": "Tornado",
        "Real_Description": "tornado",
        "Virtual_Description": "1"
    },

    # Clear
    "800": {
        "Main": "Clear",
        "Real_Description": "clear sky",
        "Virtual_Description": "0"
    },

    # Clouds
    "801": {
        "Main": "Clouds",
        "Real_Description": "few clouds: 11-25%",
        "Virtual_Description": "0.25"
    },
    "802": {
        "Main": "Clouds",
        "Real_Description": "scattered clouds: 25-50%",
        "Virtual_Description": "0.5"
    },
    "803": {
        "Main": "Clouds",
        "Real_Description": "broken clouds: 51-84%",
        "Virtual_Description": "0.75"
    },
    "804": {
        "Main": "Clouds",
        "Real_Description": "overcast clouds: 85-100%",
        "Virtual_Description": "1"
    }
}


def generate_map():
    b = json.dumps(weather_map, indent=4)
    file = open('Weather_Map.json', 'w')
    file.write(b)
    file.close()


def process_origin_data():
    real_weather = open('SanFrancisco_2021-7-24-original.json', 'r')
    content = real_weather.read()
    real_weather = json.loads(s=content)

    nanjing_weather = {}
    for i in range(len(real_weather['list'])):
        # print(real_weather['list'][i]['dt'])
        nanjing_weather.update({str(real_weather['list'][i]['dt']): real_weather['list'][i]})

    b = json.dumps(nanjing_weather, indent=4)
    file = open('SanFrancisco_2021-7-24.json', 'w')
    file.write(b)
    file.close()


def read_real_weather(time_stamp):
    real_weather = open('Nanjing_Weather_Used(7_8_Rain).json', 'r')
    content = real_weather.read()
    real_weather = json.loads(s=content)
    humidity = real_weather[time_stamp]['main']['humidity']
    clouds = real_weather[time_stamp]['clouds']['all']
    weather_id = real_weather[time_stamp]['weather'][0]['id']
    print(humidity, clouds, weather_id)
    return humidity, clouds, weather_id


def map_real_to_virtual(time_stamp):
    weather_Map = open('Weather_Map.json', 'r')
    content = weather_Map.read()
    wea_map = json.loads(s=content)

    fixed = True

    rain_level = 0
    fog_level = 0
    wetness_level = 0
    cloudiness_level = 0
    damage_level = 0

    humidity, clouds, wea_id = read_real_weather(time_stamp)

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
        wetness_level = 0
        cloudiness_level = 0
        damage_level = 0

    elif 800 < wea_id < 810:
        """
        Cloud level depend on 'clouds'.
        """
        pass
    wetness_level = humidity / 200
    cloudiness_level = clouds / 100
    print('rain_level: {}, fog_level: {}, wetness_level: {}, cloudiness_level: {}, damage_level: {}, fixed: {}'.
          format(rain_level, fog_level, wetness_level, cloudiness_level, damage_level, fixed))


if __name__ == '__main__':
    # map_real_to_virtual('1625684400')

    # read_real_weather('1625673600')
    process_origin_data()
