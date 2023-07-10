#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 21/06/2023 00:11
# @Author  : Chengjie
# @File    : maximum_changes.py
# @Software: PyCharm


import json

real_weather = open('SanFrancisco_2021-7-24.json', 'r')
content = real_weather.read()
real_weather = json.loads(s=content)
print(real_weather)
wetness = []

keys = list(real_weather.keys())
print(keys)
for i in range(len(keys) - 1):
    # for j in range(1, len(keys)):
    wetness.append(abs(real_weather[keys[i + 1]]['main']['humidity'] - real_weather[keys[i]]['main']['humidity']))

print(max(wetness))
