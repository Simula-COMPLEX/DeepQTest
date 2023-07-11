# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/16 10:47
# @Author  : Chengjie
# @File    : training_utils.py

import os

import numpy as np
import math
import requests
import torch


def calculate_reward(reward_info):
    """
    TTC_Reward, Collision_Speed_Reward, Comfortable_Reward
    :param reward_info:
    :return:
    """

    TTC = np.array(reward_info['TTC']).min()
    JERK = np.array(reward_info['JERK']).max()
    distance = np.array(reward_info['distance']).min() if reward_info['collision_type'] == 'None' else 0
    collision_speed = reward_info['collision_speed']
    if collision_speed == 0:
        Collision_Speed_Reward = 0
    else:
        Collision_Speed_Reward = collision_speed

    """
    TTC Reward
    """
    if 0 < TTC <= 7:
        TTC_Reward = -math.log(TTC / 7)
    else:
        TTC_Reward = -1

    """
    jerk reward used
    """
    if JERK > 5:
        JERK_Reward = math.exp((JERK - 0) / (0.9 - 0)) - 1
    else:
        JERK_Reward = -1  # 0.1
    """
    Dis reward used
    """
    if 0 <= distance <= 10:
        distance_Reward = -math.log(distance / 10)
    else:
        distance_Reward = -1

    final_reward = distance_Reward

    return final_reward, [TTC, collision_speed, JERK, distance], TTC_Reward, Collision_Speed_Reward, JERK_Reward


latitude_space = []
check_num = 5
latitude_position = 0

position_space = []
position_space_size = 0


def judge_not_moving_done():
    global position_space_size
    global position_space
    judge = False
    position = requests.get("http://127.0.0.1:5000/deepqtest/lgsvl-api/ego/position").json()
    position_space.append((position['x'], position['y'], position['z']))
    position_space_size = (position_space_size + 1) % check_num
    if len(position_space) == 5:
        start_pos = position_space[0]
        end_pos = position_space[4]
        position_space = []
        dis = pow(
            pow(start_pos[0] - end_pos[0], 2) + pow(start_pos[1] - end_pos[1], 2) + pow(start_pos[2] - end_pos[2], 2),
            0.5)
        if dis < 0.15:
            judge = True
    return judge


def step(actionID, env, action_space, experiment_stamp):
    reward_info = env.step(action_space[str(actionID.item() + 1)]['API'])
    action_reward, TCJD, _, _, _ = calculate_reward(reward_info)
    im, bi, sp, timestamp = env.observe_multimodal(experiment_stamp)
    # im, bi, sp, timestamp = None, None, None, None

    arrived = requests.get("http://127.0.0.1:5000/deepqtest/lgsvl-api/ego/ego-arrived").json()
    if arrived == 'True' or reward_info['collision_type'] != 'None' or judge_not_moving_done():
        episode_done = True
    else:
        episode_done = False

    return im, bi, sp, timestamp, action_reward, TCJD, reward_info, episode_done


def initialization(enable='True', simulationtime=3, date='2021-7-8', time='6:00:00', city='SanFrancisco', road_start='road1_start',
                   destination=(-300.34, 10.20, -14.54)):

    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/realistic-scenario-constraints?enable={}".format(
        enable))
    requests.post(
        "http://127.0.0.1:5000/deepqtest/lgsvl-api/set-simulationtime?simulationtime={}".format(simulationtime))
    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/load-map?map={}&road_start={}".format('SanFrancisco', road_start))
    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/set-datetime?date={}&time={}".format(date, time))
    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/load-city-weather?city={}&date={}".format(city, date))

    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/connect-dreamview")
    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/enable-modules")
    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/set-destination?des_x={}&des_y={}&des_z={}".format(
        destination[0], destination[1], destination[2]))


t = 0


def reloadEnv(date='2021-7-8', time='6:00:00', road_start='road1_start', destination=(-300.34, 10.20, -14.54),
              weather_name='Default', episode=0, road_num='1'):
    global t
    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/real-effect-info/"
                  "weather-episode?weather_name={}&episode={}&road_n={}".format(weather_name, str(episode), road_num))
    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/load-map?map={}&road_start={}".format('SanFrancisco', road_start))

    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/set-datetime?date={}&time={}".format(date, time))
    if t % 4 == 0:
        requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/connect-dreamview")
        requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/enable-modules")
        requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/set-destination?des_x={}&des_y={}&des_z={}".format(
            destination[0], destination[1], destination[2]))

    t += 1


def load_model(initial_model, model_ID, model_path, directory):
    if model_ID == -1:
        return False
    eval_net_path = model_path + "/{}/eval_net_".format(directory) + str(model_ID + 1) + '.pt'
    target_net_path = model_path + "/{}/target_net_".format(directory) + str(model_ID + 1) + '.pt'
    initial_model.eval_net.load_state_dict(torch.load(eval_net_path))
    initial_model.target_net.load_state_dict(torch.load(target_net_path))
    print('load model {} successfully.'.format(model_ID + 1))
    if directory == 'Exception':
        replay_memory = model_path + '/{}/memory'.format(directory) + str(model_ID + 1) + '.pt'
        initial_model.memory = torch.load(replay_memory)
        initial_model.steps_done = initial_model.memory.total_steps
        print('load memory {} successfully, memory size {}.'.format(model_ID + 1, len(initial_model.memory)))
    return True


def save_model(current_model, episode, model_path, directory, save_memory=True):
    if not os.path.exists(model_path + '/{}'.format(directory)):
        os.makedirs(model_path + '/{}'.format(directory))
    eval_model_path = model_path + "/{}/eval_net_".format(directory) + str(episode + 1) + '.pt'
    target_model_path = model_path + "/{}/target_net_".format(directory) + str(episode + 1) + '.pt'
    torch.save(current_model.eval_net.state_dict(), eval_model_path)
    torch.save(current_model.target_net.state_dict(), target_model_path)

    if save_memory:
        memory_path = model_path + '/{}/memory'.format(directory) + str(episode + 1) + '.pt'
        torch.save(current_model.memory, memory_path)

