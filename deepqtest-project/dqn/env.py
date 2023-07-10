# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/4/15 17:32
# @Author  : Chengjie
# @File    : env.py

from RESTAPI.LGSVLAPI6.restapi_utils import ProcessImage, ProcessLidar
import requests
import time
import torch
import numpy as np

# path = "D:/RTCM COPY/DeepCollision Journal/experiment"
path = '/home/chengjie/Chengjie/experiment'


class Env:

    def __init__(self):
        # requests.post("http://127.0.0.1:5000/simplexity-lab/lgsvl-api/load-scene", "SanFrancisco")
        requests.post(
            "http://127.0.0.1:5000/simplexity-lab/lgsvl-api/load-scene?scene={}&road_start={}".format('SanFrancisco', 'road1_start'))
        # requests.post("http://127.0.0.1:5000/simplexity-lab/lgsvl-api/load-vehicle", "LGSVL__VEHICLE_0")
        requests.post("http://127.0.0.1:5000/simplexity-lab/lgsvl-api/connect-dreamview")
        requests.post("http://127.0.0.1:5000/simplexity-lab/lgsvl-api/enable-modules")
        print('Environment initialization finished.')

    @staticmethod
    def observe():
        """
        Stat representation m1: Get four frames.
        :return:
        """
        time_stamp = str(int(time.time()))
        requests.get(
            "http://127.0.0.1:5000/simplexity-lab/lgsvl-api/sensor/camera?tag=" + time_stamp + "&frames=4").json()
        # path = '../restapi/svlapis/Image/Main_Camera/'
        state = ProcessImage.get_four_frames(path, time_stamp)
        state = state.transpose((2, 0, 1))
        state = torch.from_numpy(state)
        return state.unsqueeze(0)

    @staticmethod
    def observe_bird_view():
        bird_view = pyautogui.screenshot(region=[800, 800, 2000, 1200])
        # bird_view.show()
        return bird_view

    @staticmethod
    def observe_multimodal(experiment_stamp):
        """
        In our current implementation, this observation function is used.
        :return:
        """
        # requests.post("http://127.0.0.1:5000/simplexity-lab/lgsvl-api/npc/vehicle/randomly")
        # requests.post("http://127.0.0.1:5000/simplexity-lab/lgsvl-api/resume?simulationTime=10")
        time_stamp = str(int(time.time()))
        requests.get(
            "http://127.0.0.1:5000/simplexity-lab/lgsvl-api/sensor/camera?tag={}&frames={}&experiment={}".format(time_stamp, 1, experiment_stamp)).json()

        requests.get("http://127.0.0.1:5000/simplexity-lab/lgsvl-api/sensor/lidar?tag={}&experiment={}".format(time_stamp, experiment_stamp)).json()

        speed = np.array([round(requests.get("http://127.0.0.1:5000/simplexity-lab/lgsvl-api/sensor/speed").json(), 3)])

        # path_image = '../restapi/svlapis/Image/Main_Camera/' + '0_' + time_stamp + '.jpg'  # time_stamp
        # path_lidar = '../restapi/svlapis/Lidar/lidar_' + time_stamp + '.pcd'

        path_image = path + '/{}/Image/Main_Camera/'.format(experiment_stamp) + '0_' + time_stamp + '.jpg'  # time_stamp
        path_lidar = path + '/{}/Lidar/lidar_'.format(experiment_stamp) + time_stamp + '.pcd'

        # print('im time, lidar time: {}, {}'.format(im_end - im_start, lidar_end - lidar_start))

        im = ProcessImage.get_RGB_image(path_image)

        birdView = ProcessLidar.get_lidar_bird_view(path_lidar)
        # print('im time, lidar time: {}, {}'.format(im_end - im_start, lidar_end - lidar_start))

        return torch.from_numpy(im.transpose((2, 0, 1))).unsqueeze(0), torch.from_numpy(
            birdView.transpose((2, 0, 1))).unsqueeze(0), torch.from_numpy(speed).unsqueeze(0), time_stamp
        # return im, birdView, speed

    @staticmethod
    def step(restapi):
        probability_list = requests.post(restapi).json()
        return probability_list


if __name__ == "__main__":

    print(str(int(time.time())))
