# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/13 9:56
# @Author  : Chengjie
# @File    : __init__.py

import requests
import numpy as np

a = [11, 1, 1, 1]
print(np.array(a).max())

# a = requests.get('https://app.dignio.com/app/common/directives/filterBar/select.filterbar.html?_=bd636b800')
# print(a, '\n', a.content)

# b = requests.post('https://www.google-analytics.com/j/collect?v=1&_v=j96&aip=1&a=1087315191&t=pageview&_s=1&dl=https'
#                   '%3A%2F%2Fdeveloper.mozilla.org%2Fen-US%2Fdocs%2FWeb%2FHTTP%2FStatus%2F408&dr=https%3A%2F%2Fwww'
#                   '.google.com%2F&ul=en&de=UTF-8&dt=408%20Request%20Timeout%20-%20HTTP%20%7C%20MDN&sd=30-bit&sr'
#                   '=1512x982&vp=509x770&je=0&_u=YEBAAAABAAAAAC~&jid=2001975461&gjid=2016446622&cid=1591534337'
#                   '.1662641049&tid=UA-36116321-5&_gid=1707858304.1662641049&_r=1&_slc=1&z=1576261263?v=1&_v=j96&aip=1'
#                   '&a=1087315191&t=pageview&_s=1&dl=https%3A%2F%2Fdeveloper.mozilla.org%2Fen-US%2Fdocs%2FWeb%2FHTTP'
#                   '%2FStatus%2F408&dr=https%3A%2F%2Fwww.google.com%2F&ul=en&de=UTF-8&dt=408%20Request%20Timeout%20'
#                   '-%20HTTP%20%7C%20MDN&sd=30-bit&sr=1512x982&vp=509x770&je=0&_u=YEBAAAABAAAAAC~&jid=2001975461&gjid'
#                   '=2016446622&cid=1591534337.1662641049&tid=UA-36116321-5&_gid=1707858304.1662641049&_r=1&_slc=1&z'
#                   '=1576261')
# print(b)
# ?login=kostas@simula.no&password=M3asN3tw
payload = {'login': 'kostas@simula.no'}
a = requests.get('https://app.dignio.com/api/auth/logout')
print(a)

headers = {
    'authority': 'app.dignio.com',
    'method': 'POST',
    'path': "/api/auth/factors/email?return_auth_info",
    'scheme': 'https',
    'accept': 'application/json, text/plain, */*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en,zh-CN;q=0.9,zh;q=0.8',
    'content-length': "34",
    'content-type': 'application/json;charset=UTF-8',
    'origin': 'https://app.dignio.com',
    'sec-ch-ua': "Google Chrome;v=105, Not)A;Brand;v=8, Chromium;v=105",
    'sec-ch-ua-mobile': "?0",
    'sec-ch-ua-platform': "macOS",
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/105.0.0.0 Safari/537.36 '
}

res = requests.post('https://app.dignio.com/api/auth/factors/email?return_auth_info=kostas@simula.no', headers=headers)
print(res)
