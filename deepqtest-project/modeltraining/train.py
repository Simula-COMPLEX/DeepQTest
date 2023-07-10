# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/18 9:28
# @Author  : Chengjie
# @File    : train.py
import time

from restapi.apilibrary.api_utils import get_action_space
from restapi.svlapis.road_weather import roads, real_world_weather
from itertools import count
from dqn.multi_modal_model import HyperParameter, DQN
from dqn.env import Env

import pandas as pd
from modeltraining.training_utils import *

env = Env()

IM, BIRD, SPEED, _ = env.observe_multimodal('Initialization')
_, _, IM_HEIGHT, IM_WIDTH = IM.shape
_, _, BIRD_HEIGHT, BIRD_WIDTH = BIRD.shape
action_space = get_action_space('environment_configuration_apis')
N_ACTION = action_space['number']
print('Action space size: ', N_ACTION)

save = True
title = ["Episode", "Step", "State", "Action", "Reward", "Reward_Info", "Done"]
df_title = pd.DataFrame([title])


def train(road, effect, effect_n, reward_type):
    EPISODE = 600
    experiment_tag = 'experiment({})_{}reward_{}'.format(road['description'], reward_type, effect_n)

    filename = './trainingData/formal_experiment_data/{}.csv'.format(experiment_tag)
    model_path = "../experiment/{}/model".format(experiment_tag)
    dqn = DQN(IM_HEIGHT, IM_WIDTH, BIRD_HEIGHT, BIRD_WIDTH, N_ACTION)
    episode_count = 0
    try:
        episode_start = 0
        model_ID = -1 if episode_start == 0 else episode_start  # -1 if do not need to load model
        # directory = "Exception"
        directory = "Trained"
        load = load_model(dqn, model_ID, model_path, directory)  #
        if save and not load:
            df_title.to_csv(filename, mode='w', header=False, index=False)

        initialization(time=effect['time'], date=effect['date'], city=effect['city'], road_start=road['start'],
                       destination=road['destination'], simulationtime=3)
        print('Set simulation time to ' + str(3) + ' second(s).')

        print('Start training dqn model on {} ...'.format(road['description']))
        optimize_flag = True
        step_done = 0
        for i_episode in range(episode_start, EPISODE):
            episode_count = i_episode
            print('------------------------------------------------------')
            print('+                    Episode: ', i_episode, '                   +')
            print('------------------------------------------------------')
            reloadEnv(time=effect['time'], date=effect['date'], road_start=road['start'],
                      destination=road['destination'])
            image, bird, speed, timestamp = env.observe_multimodal(experiment_tag)
            total_reward = 0.0

            if (i_episode + 1) % 50 == 0 and (i_episode + 1) > 400:
                print('saved model: ' + str(i_episode + 1))
                save_model(dqn, i_episode, model_path, "Trained", save_memory=False)

            for st in count():
                action, step_done = dqn.select_action(image.to(dqn.device), bird.to(dqn.device), speed.to(dqn.device))

                image_, bird_, speed_, timestamp_, reward, tcjd, reward_info_, done = step(action, env, action_space,
                                                                                           experiment_tag)
                total_reward += reward
                if not done:
                    next_image, next_bird, next_speed = image_, bird_, speed_
                else:
                    next_image, next_bird, next_speed = None, None, None

                reward = torch.tensor([reward], device=dqn.device)
                dqn.memory.push(image, bird, speed, action.to(dqn.device), next_image, next_bird, next_speed,
                                reward.to(dqn.device))

                print('>>>>>>>>>>step: {}, action: {}, reward: {}, TTC_SAC_JERK_Distance: {}, done: {}.'.
                      format(st, action.item(), round(reward.item(), 3), tcjd, done))
                if save:
                    pd.DataFrame([[i_episode, st, {'Image&LidarTimeStamp': timestamp, 'speed': speed.item()},
                                   action.item(), reward.item(), reward_info_, done]]). \
                        to_csv(filename, mode='a', header=False, index=False)

                image, bird, speed = next_image, next_bird, next_speed
                timestamp = timestamp_

                if step_done > HyperParameter['INITIAL_MEMORY']:
                    if optimize_flag:
                        print('starting optimizing...')
                        optimize_flag = False
                    dqn.optimize_model()

                    if step_done % HyperParameter['TARGET_UPDATE'] == 0:
                        dqn.target_net.load_state_dict(dqn.eval_net.state_dict())

                if done:
                    print("Finished Episode {} with total reward {}".format(i_episode, total_reward))
                    break
            if step_done > 9000 and i_episode > 600:
                break
    except Exception as e:
        import traceback
        print('error occurred, saving breakpoint #{}. Error details: {}'.format(episode_count, e))
        traceback.print_exc()
        save_model(dqn, episode_count, model_path, "Exception", save_memory=True)
        print('Breakpoint saved.')


if __name__ == '__main__':
    print('training start at {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))

    for weather in real_world_weather.keys():
        for ro in roads:
            start = time.time()
            train(roads[ro], real_world_weather[weather], weather, 'TTC')
            end = time.time()
            print('training time is {} h.'.format((end - start) / 60 / 60))
