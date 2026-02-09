# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/4/15 20:48
# @Author  : Chengjie
# @File    : api_utils.py

import json
import os

path = os.path.dirname(os.path.realpath(__file__))
# print(path)


def get_action_space(api_file):
    filename = path + '/{}.json'.format(api_file)  # '/environment_configuration_apis.json'
    json_file = open(filename, 'r')
    content = json_file.read()
    restful_apis = json.loads(s=content)
    return restful_apis


if __name__ == '__main__':
    print(get_action_space('environment_configuration_apis')['number'])
