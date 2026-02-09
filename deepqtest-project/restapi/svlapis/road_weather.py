# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/15 22:21
# @Author  : Chengjie
# @File    : road_weather.py


real_world_weather = {
    'rainy-day': {
        'time': '8:00:00',
        'date': '2021-7-8'
    },

    'rainy-night': {
        'time': '20:00:00',
        'date': '2021-7-8'
    },
    'sunny-day': {
        'time': '8:00:00',
        'date': '2021-7-24'
    },
    'sunny-night': {
        'time': '20:00:00',
        'date': '2021-7-24'
    },

}

roads = {
    'road1': {
        'num': '1',
        'start': 'road1_start',
        'destination': (-300.34, 10.20, -14.54),
        'description': 'road1'
    },
    'road2': {
        'num': '2',
        'start': 'road2_start',
        'destination': (-456.89, 10.20, -231.05),
        'description': 'road2'
    },
    'road3': {
        'num': '3',
        'start': 'road3_start',
        'destination': (-248.69, 10.20, -421.14),
        'description': 'road3'
    },
    'road4': {
        'num': '4',
        'start': 'road4_start',
        'destination': (-262.04, 10.20, -243.00),
        'description': 'road4'
    }
}
