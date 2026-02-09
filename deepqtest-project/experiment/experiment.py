import json
import random
import socket

from restapi.apilibrary.api_utils import get_action_space
from restapi.svlapis.road_weather import roads, real_world_weather
from itertools import count
from dqn.multi_modal_model import DQN
from dqn.env import Env

import pandas as pd
import time
from modeltraining.training_utils import *

env = Env()

IM, BIRD, SPEED, _ = env.observe_multimodal('Initialization')
_, _, IM_HEIGHT, IM_WIDTH = IM.shape
_, _, BIRD_HEIGHT, BIRD_WIDTH = BIRD.shape
#
action_space = get_action_space('environment_configuration_apis')
N_ACTION = action_space['number']  # N_ACTION = 142
print('Action space size: ', N_ACTION)

save = True
title = ["Episode", "Step", "State", "Action", "Reward", "Reward_Info",
         "Ego_Vehicle_Ops_Value", "Ego_Vehicle_Pose", "Obstacle_Info", "Traffic_Light", "Done"]
df_title = pd.DataFrame([title])

HOST = 'localhost'
PORT = 6001
ADDR = (HOST, PORT)

ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ss.connect(ADDR)

judge = True


def greedy_Exp(road, effect, effect_n, reward_type):
    experiment_tag = 'Greedy_Experiment({})_{}Reward_{}'.format(road['description'], reward_type, effect_n)
    filename = './testingData/formal_experiment_data/Greedy/{}.csv'.format(experiment_tag)
    global judge
    try:
        episode_start = 0
        episode_end = 19
        if episode_start == 0:
            df_title.to_csv(filename, mode='w', header=False, index=False)

        initialization(time=effect['time'], date=effect['date'], city=effect['city'], road_start=road['start'],
                       destination=road['destination'], simulationtime=3)
        print('Set Observation period to ' + str(3) + ' second(s).')
        print('Start running greedy strategy: {} ...'.format(experiment_tag))

        st = 0

        reloadEnv(time=effect['time'], date=effect['date'], road_start=road['start'],
                  destination=road['destination'], weather_name="Greedy_" + effect_n, episode=episode_start)
        requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/savestate?ID={}".format(st))

        total_reward = 0.0
        print('------------------------------------------------------')
        print('+                    Episode: ', episode_start, '                   +')
        print('------------------------------------------------------')

        while True:
            metric_temp = 100000  # metric can be TTC (min), Distance (min), Jerk (max)
            new_api = torch.tensor(0)
            for api in range(0, N_ACTION):  # N_ACTION
                action = torch.tensor(api)
                requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/save-scenario?save={}".format('False'))
                image_, bird_, speed_, timestamp_, reward, tcjd, reward_info_, done = step(action, env, action_space,
                                                                                           experiment_tag)  # tcjd: [TTC, collision_speed, JERK, distance]

                if tcjd[3] < metric_temp:  # Jerk Reward [2] >
                    metric_temp = tcjd[3]
                    new_api = action
                requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/rollback?ID={}".format(st))

            """
            Searching finished, starting to run new_api
            """
            image, bird, speed, timestamp = env.observe_multimodal(experiment_tag)
            # image, bird, speed, timestamp = None, None, torch.tensor(-1), None
            ss.send(json.dumps(['start']).encode('utf-8'))
            requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/save-scenario?save={}".format('True'))

            image_, bird_, speed_, timestamp_, reward, tcjd, reward_info_, done = step(new_api, env, action_space,
                                                                                       experiment_tag)

            ss.send(json.dumps(['stop']).encode('utf-8'))

            """
            Processing start
            """
            cmd_res_size = ss.recv(1024)
            length = int(cmd_res_size.decode())
            ss.send(json.dumps(['confirmed']).encode('utf-8'))
            received_size = 0
            received_data = b''
            while received_size < length:
                cmd_res = ss.recv(1024)
                received_size += len(cmd_res)
                received_data += cmd_res
            received_data = json.loads(received_data.decode('utf-8'))
            state_arr = received_data['state_arr']
            pose_arr = received_data['pose_arr']
            obstacle_arr = received_data['obstacle_arr']
            traffic_light = received_data['traffic_light']
            """
            Processing end
            """

            print('>>>>>>>>>>step: {}, action: {}, reward: {}, TTC_SAC_JERK_Distance: {}, done: {}.'.
                  format(st, new_api.item(), round(reward, 3), tcjd, done))
            if save:
                pd.DataFrame([[episode_start, st, {'Image&LidarTimeStamp': timestamp, 'speed': speed.item()},
                               new_api.item(), reward, reward_info_,
                               state_arr, pose_arr, obstacle_arr, traffic_light, done]]). \
                    to_csv(filename, mode='a', header=False, index=False)
            st += 1

            requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/savestate?ID={}".format(st))

            total_reward += reward
            if done:
                print("Finished Episode {} with total reward {}".format(episode_start, total_reward))
                episode_start += 1
                st = 0
                if episode_start == episode_end:
                    break

                print('------------------------------------------------------')
                print('+                    Episode: ', episode_start, '                   +')
                print('------------------------------------------------------')

    except Exception as e:
        import traceback
        print('error occurred, saving breakpoint #{}. Error details: {}'.format('episode_count', e))
        traceback.print_exc()
        print('Saved.')


def random_exp(road, effect, effect_n, reward_type):
    EPISODE = 20
    experiment_tag = 'Random_Experiment({})_{}Reward_{}'.format(road['description'], reward_type, effect_n)

    filename = './testingData/formal_experiment_data/Random/{}.csv'.format(experiment_tag)
    episode_count = 0

    try:
        episode_start = 0
        df_title.to_csv(filename, mode='w', header=False, index=False)

        initialization(time=effect['time'], date=effect['date'], city=effect['city'], road_start=road['start'],
                       destination=road['destination'], simulationtime=3)
        print('Set Observation period to ' + str(3) + ' second(s).')

        print('Start running random strategy on {} ...'.format(road['description']))
        for i_episode in range(episode_start, EPISODE):

            episode_count = i_episode
            print('------------------------------------------------------')
            print('+                    Episode: ', i_episode, '                   +')
            print('------------------------------------------------------')
            reloadEnv(time=effect['time'], date=effect['date'], road_start=road['start'],
                      destination=road['destination'], weather_name="Random_" + effect_n,
                      episode=i_episode, road_num=road['num'])
            image, bird, speed, timestamp = env.observe_multimodal(experiment_tag)
            total_reward = 0.0

            for st in count():
                # s = time.time()
                action = torch.tensor(random.randint(0, N_ACTION - 1))

                ss.send(json.dumps(['start']).encode('utf-8'))
                image_, bird_, speed_, timestamp_, reward, tcjd, reward_info_, done = step(action, env, action_space,
                                                                                           experiment_tag)
                ss.send(json.dumps(['stop']).encode('utf-8'))

                """
                Processing start
                """
                cmd_res_size = ss.recv(1024)
                length = int(cmd_res_size.decode())
                ss.send(json.dumps(['confirmed']).encode('utf-8'))
                received_size = 0
                received_data = b''
                while received_size < length:
                    cmd_res = ss.recv(1024)
                    received_size += len(cmd_res)
                    received_data += cmd_res
                received_data = json.loads(received_data.decode('utf-8'))
                state_arr = received_data['state_arr']
                pose_arr = received_data['pose_arr']
                obstacle_arr = received_data['obstacle_arr']
                traffic_light = received_data['traffic_light']
                """
                Processing end
                """

                total_reward += reward
                if not done:
                    next_image, next_bird, next_speed = image_, bird_, speed_
                else:
                    next_image, next_bird, next_speed = None, None, None

                print('>>>>>>>>>>step: {}, action: {}, reward: {}, TTC_SAC_JERK_Distance: {}, done: {}.'.
                      format(st, action.item(), round(reward, 3), tcjd, done))
                if save:
                    pd.DataFrame([[i_episode, st, {'Image&LidarTimeStamp': timestamp, 'speed': speed.item()},
                                   action.item(), reward, reward_info_,
                                   state_arr, pose_arr, obstacle_arr, traffic_light, done]]). \
                        to_csv(filename, mode='a', header=False, index=False)

                image, bird, speed = next_image, next_bird, next_speed
                timestamp = timestamp_

                if done:
                    print("Finished Episode {} with total reward {}".format(i_episode, total_reward))
                    break

    except Exception as e:
        import traceback
        print('error occurred, saving breakpoint #{}. Error details: {}'.format(episode_count, e))
        traceback.print_exc()
        print('Saved.')
        exit(1)


def dqn_exp(road, effect, effect_n, reward_type):
    EPISODE = 20
    experiment_tag = 'experiment({})_{}Reward_{}'.format(road['description'], reward_type, effect_n)

    filename = './testingData/formal_experiment_data/dqn/{}.csv'.format(experiment_tag)
    model_path = "../experiment/{}/Model".format(experiment_tag)
    print(model_path)
    dqn = DQN(IM_HEIGHT, IM_WIDTH, BIRD_HEIGHT, BIRD_WIDTH, N_ACTION)  # (160 376 300 300 194)
    episode_count = 0

    try:
        episode_start = 0
        model_ID = -1
        directory = "Trained"
        load_model(dqn, model_ID, model_path, directory)  #

        initialization(time=effect['time'], date=effect['date'], city=effect['city'], road_start=road['start'],
                       destination=road['destination'], simulationtime=3)
        print('Set Observation period to ' + str(3) + ' second(s).')

        print('Start training dqn model on {} ...'.format(road['description']))

        for i_episode in range(episode_start, EPISODE):

            episode_count = i_episode
            print('------------------------------------------------------')
            print('+                    Episode: ', i_episode, '                   +')
            print('------------------------------------------------------')
            reloadEnv(time=effect['time'], date=effect['date'], road_start=road['start'],
                      destination=road['destination'], weather_name="DQN_" + effect_n,
                      episode=i_episode, road_num=road['num'])
            image, bird, speed, timestamp = env.observe_multimodal(experiment_tag)
            total_reward = 0.0

            for st in count():
                action, step_done = dqn.select_action(image.to(dqn.device), bird.to(dqn.device), speed.to(dqn.device))
                ss.send(json.dumps(['start']).encode('utf-8'))
                image_, bird_, speed_, timestamp_, reward, tcjd, reward_info_, done = step(action, env, action_space,
                                                                                           experiment_tag)
                ss.send(json.dumps(['stop']).encode('utf-8'))

                """
                Processing start
                """
                cmd_res_size = ss.recv(1024)
                length = int(cmd_res_size.decode())
                ss.send(json.dumps(['confirmed']).encode('utf-8'))
                received_size = 0
                received_data = b''
                while received_size < length:
                    cmd_res = ss.recv(1024)
                    received_size += len(cmd_res)
                    received_data += cmd_res
                received_data = json.loads(received_data.decode('utf-8'))
                state_arr = received_data['state_arr']
                pose_arr = received_data['pose_arr']
                obstacle_arr = received_data['obstacle_arr']
                traffic_light = received_data['traffic_light']
                """
                Processing end
                """

                total_reward += reward
                if not done:
                    next_image, next_bird, next_speed = image_, bird_, speed_
                else:
                    next_image, next_bird, next_speed = None, None, None

                reward = torch.tensor([reward], device=dqn.device)

                print('>>>>>>>>>>step: {}, action: {}, reward: {}, TTC_SAC_JERK_Distance: {}, done: {}.'.
                      format(st, action.item(), round(reward.item(), 3), tcjd, done))
                if save:
                    pd.DataFrame([[i_episode, st, {'Image&LidarTimeStamp': timestamp, 'speed': speed.item()},
                                   action.item(), reward.item(), reward_info_,
                                   state_arr, pose_arr, obstacle_arr, traffic_light, done]]). \
                        to_csv(filename, mode='a', header=False, index=False)

                image, bird, speed = next_image, next_bird, next_speed
                timestamp = timestamp_

                if done:
                    print("Finished Episode {} with total reward {}".format(i_episode, total_reward))
                    break

    except Exception as e:
        import traceback
        print('error occurred, saving breakpoint #{}. Error details: {}'.format(episode_count, e))
        traceback.print_exc()
        print('Saved.')
        exit(1)


if __name__ == '__main__':
    print('testing start at {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))

    weathers = real_world_weather.keys()

    for ro in roads:
        for wea in weathers:
            start = time.time()
            # dqn_exp(roads[ro], real_world_weather[wea], wea, 'TTC')
            greedy_Exp(roads[ro], real_world_weather[wea], wea, 'Distance')
            # random_exp(roads[ro], real_world_weather[wea], wea, 'TTC')
            end = time.time()
            print('testing time is {} h.'.format((end - start) / 60 / 60))
