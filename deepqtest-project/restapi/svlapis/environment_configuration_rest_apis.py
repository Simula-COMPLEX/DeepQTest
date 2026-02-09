# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/4/15 17:32
# @Author  : Chengjie
# @File    : environment_configuration_rest_apis.py


import math
import queue
import random
import json
import os
import socket

import lgsvl
import time
import torch
from datetime import datetime

import requests
from flask import Flask, request
from datetime import timedelta
from environs import Env
from lgsvl.dreamview import CoordType

from restapi.svlapis.restapi_utils import ProcessImage
from restapi.svlapis.collision_utils import pedestrian, npc_vehicle, calculate_TTC
from restapi.svlapis.weather_utils import map_real_to_virtual

from scenariocollector.create_utils import *

env = Env()

T = 3  # simulation time
time_step = 0.5  # time step
SENSORS = None
EGO = None
DREAMVIEW = None
CONSTRAINTS = True
CONTROL = False
DATETIME_UNIX = None
WEATHER_DATA = None
TIMESTAMP = None
DESTINATION = None
SAVE_SCENARIO = True

WEATHER_NAME = 'Default'
EPISODE = 0
ROAD = 'Road1'

HOST = 'localhost'
PORT = 6002
ADDR = (HOST, PORT)

ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ss.connect(ADDR)

NPC_QUEUE = queue.Queue(maxsize=20)
CONE = []
ProcessImageUtil = ProcessImage(SENSORS)
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

sim = lgsvl.Simulator(env.str("LGSVL__SIMULATOR_HOST", lgsvl.wise.SimulatorSettings.simulator_host),
                      env.int("LGSVL__SIMULATOR_PORT", lgsvl.wise.SimulatorSettings.simulator_port))

BRIDGE_HOST = os.environ.get("BRIDGE_HOST", "127.0.0.1")
BRIDGE_PORT = int(os.environ.get("BRIDGE_PORT", 9090))
MODULES = [
    'Localization',
    'Perception',
    'Transform',
    'Routing',
    'Prediction',
    'Planning',
    'Traffic Light',
    'Control'
]

print('REST APIs Connected.')
prefix = '/deepqtest/lgsvl-api/'

"""
util functions
"""

collision_object = None
collision_tag = False
collision_speed = 0

JERK = 0

probability = 0
z_axis = lgsvl.Vector(0, 0, 100)
u = 0.6


def on_collision(agent1, agent2, contact):
    name1 = agent1.__dict__.get('name')
    name2 = agent2.__dict__.get('name') if agent2 is not None else "OBSTACLE"
    print("{} collided with {} at {}".format(name1, name2, contact))
    global collision_object
    global collision_speed
    global collision_tag
    collision_object = name2
    collision_tag = True
    try:
        collision_speed = agent1.state.speed
    except KeyError:
        collision_speed = -1
        print('KeyError')


def calculate_measures(agents, ego):
    global probability
    global DATETIME_UNIX
    global collision_tag

    probability = 0

    global collision_object
    global collision_speed
    global TIMESTAMP

    collision_object = None
    collision_speed = 0

    TTC_list = []
    JERK_list = []
    distance_list = []
    i = 0
    speed = 0

    if SAVE_SCENARIO:
        doc, root = initialization(str(sim.current_datetime), get_time_stamp(), './{}.json'.format(WEATHER_NAME))
        entities, storyboard = initializeStory(agents, doc, root)
        story = doc.createElement('Story')
        story.setAttribute('name', 'Default')

    while i < T / time_step:
        ss.send('acc_start'.encode('utf-8'))
        acc_old = float(ss.recv(1024).decode('utf-8'))
        new_time_stamp = get_time_stamp()
        if TIMESTAMP != new_time_stamp:
            TIMESTAMP = new_time_stamp
            weather = map_real_to_virtual(new_time_stamp, WEATHER_DATA)
            sim.weather = lgsvl.WeatherState(rain=weather[0], fog=weather[1], wetness=weather[2],
                                             cloudiness=weather[3],
                                             damage=weather[4])
        if SAVE_SCENARIO:
            create_story_by_timestamp(i + 1, doc, story, entities, agents, sim)

        sim.run(time_limit=time_step)
        ss.send('acc_start'.encode('utf-8'))
        acc_new = float(ss.recv(1024).decode('utf-8'))
        JERK_list.append(abs(acc_new - acc_old) / 0.5)
        if collision_tag:
            speed = EGO.state.speed
            print('speed at collision')
            collision_tag = False

        TTC, distance = calculate_TTC(agents, ego, SAVE_SCENARIO)
        TTC_list.append(round(TTC, 6))
        distance_list.append(round(distance, 6))
        i += 1

    collision_type, collision_speed_ = get_collision_info()
    if collision_speed_ == -1:
        collision_speed_ = speed

    if SAVE_SCENARIO:
        storyboard.appendChild(story)
        root.appendChild(storyboard)
        root.setAttribute('timestep', '0.1')

        path = '../../experiment/{}/{}'.format(ROAD, WEATHER_NAME)
        try:
            os.makedirs(path)
        except Exception as e:
            print(e)

        time_t = str(int(time.time()))

        fp = open(path + "/{}_Scenario_{}.deepscenario".format(EPISODE, time_t), "w")
        doc.writexml(fp, addindent='\t', newl='\n', encoding="utf-8")

    return {'TTC': TTC_list, 'distance': distance_list, 'collision_type': collision_type,
            'collision_speed': collision_speed_, 'JERK': JERK_list}


def set_color(color):
    colorV = lgsvl.Vector(0, 0, 0)
    if color == 'black':
        colorV = lgsvl.Vector(0, 0, 0)
    elif color == 'white':
        colorV = lgsvl.Vector(1, 1, 1)
    elif color == 'yellow':
        colorV = lgsvl.Vector(1, 1, 0)
    elif color == 'pink':
        colorV = lgsvl.Vector(1, 0, 1)
    elif color == 'skyblue':
        colorV = lgsvl.Vector(0, 1, 1)
    elif color == 'red':
        colorV = lgsvl.Vector(1, 0, 0)
    elif color == 'green':
        colorV = lgsvl.Vector(0, 1, 0)
    elif color == 'blue':
        colorV = lgsvl.Vector(0, 0, 1)
    return colorV


def get_no_conflict_position(position, car):
    if car == 'BoxTruck' or car == 'SchoolBus':
        sd = 10
    else:
        sd = 8
    generate = True
    if CONSTRAINTS:
        agents = sim.get_agents()
        for agent in agents:
            if math.sqrt(pow(position.x - agent.transform.position.x, 2) +
                         pow(position.y - agent.transform.position.y, 2) +
                         pow(position.z - agent.transform.position.z, 2)) < sd:
                generate = False
                break
    return generate


def control_agents_density(agent):
    if CONTROL:

        if NPC_QUEUE.full():
            sim.remove_agent(NPC_QUEUE.get())
            NPC_QUEUE.put(agent)
        else:
            NPC_QUEUE.put(agent)


@app.route(prefix)
def index():
    return 'REST APIs for environment control.'


@app.route(prefix + 'info/simulator-info', methods=['GET'])
def get_sim_version():
    sim_info = {"Simulator Name": "LGSVL", "Simulator Version": sim.version}
    return json.dumps(sim_info)


@app.route(prefix + 'real-world-weather-info/weather-episode', methods=['POST'])
def get_effect_info():
    global WEATHER_NAME
    global EPISODE
    global ROAD
    WEATHER_NAME = request.args.get('weather_name')
    EPISODE = int(request.args.get('episode'))
    ROAD = request.args.get('road_n')
    print(WEATHER_NAME, EPISODE, ROAD)

    return 'set real-world-weather-episode'


@app.route(prefix + 'save-scenario', methods=['POST'])
def save_scenario():
    global SAVE_SCENARIO

    SAVE_SCENARIO = (str(request.args.get('save')) == 'True')

    print(SAVE_SCENARIO)

    return 'set tag_save_scenario'


@app.route(prefix + 'set-simulationtime', methods=['POST'])
def set_simulationtime():
    global T
    T = int(request.args.get('simulationtime'))
    print('Simulation time is set to {} second(s).'.format(T))
    return json.dumps(T)


@app.route(prefix + 'load-city-weather', methods=['POST'])
def load_city_weather():
    global WEATHER_DATA
    which_city = request.args.get('city')
    which_day = request.args.get('date')
    weather_database = which_city + '_' + which_day + '.json'
    real_weather = open('./openweather-database/' + weather_database, 'r')
    content = real_weather.read()
    WEATHER_DATA = json.loads(s=content)


@app.route(prefix + 'realistic-scenario-constraints', methods=['POST'])
def set_constraints():
    global CONSTRAINTS
    flag = str(request.args.get('enable'))
    CONSTRAINTS = (flag == 'True')
    if CONSTRAINTS:
        print('Realistic-Scenario-Constraints module is enabled.')
    return str(CONSTRAINTS)


@app.route(prefix + 'set-datetime', methods=['POST'])
def set_datetime():
    date = request.args.get('date')
    timeofday = request.args.get('time')
    date_ = date.split('-')
    timeofday_ = timeofday.split(':')
    dt = datetime(int(date_[0]), int(date_[1]), int(date_[2]), int(timeofday_[0]), int(timeofday_[1]),
                  int(timeofday_[2]))
    sim.set_date_time(dt, fixed=False)
    return json.dumps({"datetime": str(dt)})


@app.route(prefix + 'load-map', methods=['POST'])
def load_scene():
    scene = request.args.get('map')
    road_start = request.args.get('road_start')

    if sim.current_scene == lgsvl.wise.DefaultAssets.map_sanfrancisco:
        sim.reset()
    else:
        sim.load(lgsvl.wise.DefaultAssets.map_sanfrancisco)

    global SENSORS
    global ProcessImageUtil
    global EGO
    global ROAD
    EGO = None

    if road_start == 'road1_start':
        ROAD = 'Road1'
    elif road_start == 'road2_start':
        ROAD = 'Road2'
    elif road_start == 'road3_start':
        ROAD = 'Road3'
    elif road_start == 'road4_start':
        ROAD = 'Road4'

    state = lgsvl.AgentState()
    state.transform = torch.load('./{}.pt'.format(road_start))
    EGO = sim.add_agent(
        env.str("LGSVL__VEHICLE_0", lgsvl.wise.DefaultAssets.ego_lincoln2017mkz_apollo5),
        lgsvl.AgentType.EGO,
        state)

    EGO.connect_bridge(env.str("LGSVL__AUTOPILOT_0_HOST", lgsvl.wise.SimulatorSettings.bridge_host),
                       env.int("LGSVL__AUTOPILOT_0_PORT", lgsvl.wise.SimulatorSettings.bridge_port))
    print("Bridge connected:", EGO.bridge_connected)
    EGO.on_collision(on_collision)
    SENSORS = EGO.get_sensors()
    ProcessImageUtil = ProcessImage(SENSORS)

    control_policy = "green=1;loop"
    signals = sim.get_controllables()
    for signal in signals:
        signal.control(control_policy)

    sim.run(0.1)

    return json.dumps(scene)


@app.route(prefix + 'reload-env', methods=['POST'])
def reset_scene():
    global CONE
    agents = sim.get_agents()
    for i in range(1, len(agents)):
        sim.remove_agent(agents[i])

    for i in range(len(CONE)):
        sim.controllable_remove(CONE[i])
    CONE = []

    spawns = sim.get_spawn()
    state = lgsvl.AgentState()
    state.transform = spawns[0]
    EGO.state = state
    sim.run(0.1)
    return 'reset ego'


@app.route(prefix + 'connect-dreamview', methods=['POST'])
def connect_dreamview():
    global DREAMVIEW
    DREAMVIEW = lgsvl.dreamview.Connection(sim, EGO, BRIDGE_HOST)
    map_ = 'san_francisco'
    vehicle = 'Lincoln2017MKZ'
    DREAMVIEW.set_hd_map(map_)
    DREAMVIEW.set_vehicle(vehicle)
    return 'connect to dreamview'


@app.route(prefix + 'enable-modules', methods=['POST'])
def enable_modules():
    global MODULES
    status = DREAMVIEW.get_module_status()
    for module in MODULES:
        if not status[module]:
            DREAMVIEW.enable_module(module)

    print('ADS modules are enabled.')
    return 'enable modules'


@app.route(prefix + 'set-destination', methods=['POST'])
def set_destination():
    global DESTINATION
    enable_modules()
    x = float(request.args.get('des_x'))
    y = float(request.args.get('des_y'))
    z = float(request.args.get('des_z'))
    DESTINATION = (x, y, z)
    DREAMVIEW.set_destination(x, z, y, coord_type=CoordType.Unity)
    return 'set destination.'


@app.route(prefix + 'resume', methods=['POST'])
def resume():
    simulation_time = int(request.args.get('simulationTime'))
    sim.run(simulation_time)
    return json.dumps(simulation_time)


@app.route(prefix + 'pause', methods=['POST'])
def pause():
    sim.stop()
    return 'paused'


@app.route(prefix + '/savestate', methods=['POST'])
def save_state():
    state_id = str(request.args.get('ID'))

    agents = sim.get_agents()
    count_ego = 0
    count_npc = 0
    count_pedestrian = 0

    states_dict = {}

    weather_dict = {}

    weather_dict.update(
        {'rain': sim.weather.rain, 'fog': sim.weather.fog, 'wetness': sim.weather.wetness, 'time': sim.time_of_day})

    for agent in agents:
        obj_name = "None"
        obj_uid = agent.uid
        print(obj_uid, type(agent.uid))
        obj_color_vector = "None"
        obj_type = get_type(agent.__class__)
        if obj_type == 'Ego':
            obj_name = 'Ego' + str(count_ego)
            obj_color_vector = str(agent.color)
            count_ego += 1
        elif obj_type == 'NPC':
            obj_name = 'NPC' + str(count_npc)
            count_npc += 1
            obj_color_vector = str(agent.color)
        elif obj_type == 'Pedestrian':
            obj_name = 'Pedestrian' + str(count_pedestrian)
            obj_color_vector = str(agent.color)
        model = agent.name

        agent_dict = {}
        agent_dict.update({'model': model, 'name:': obj_name, 'obj_color': obj_color_vector})
        agent_dict.update({'positionX': agent.state.position.x, 'positionY': agent.state.position.y,
                           'positionZ': agent.state.position.z})
        agent_dict.update({'rotationX': agent.state.rotation.x, 'rotationY': agent.state.rotation.y,
                           'rotationZ': agent.state.rotation.z})
        agent_dict.update({'velocityX': agent.state.velocity.x, 'velocityY': agent.state.velocity.y,
                           'velocityZ': agent.state.velocity.z})
        agent_dict.update(
            {'angularVelocityX': agent.state.angular_velocity.x, 'angularVelocityY': agent.state.angular_velocity.y,
             'angularVelocityZ': agent.state.angular_velocity.z})

        states_dict.update({obj_uid: agent_dict})

    states_dict.update({'weatherCondition': weather_dict})

    b = json.dumps(states_dict, indent=4)
    file = open('state/current_state_{}.json'.format(state_id), 'w')
    file.write(b)
    file.close()
    return 'saved successfully'


@app.route(prefix + '/rollback', methods=['POST'])
def roll_back():
    state_ID = str(request.args.get('ID'))
    state = open('state/current_state_{}.json'.format(state_ID), 'r')
    content = state.read()
    state_ = json.loads(content)
    sim.weather = lgsvl.WeatherState(rain=state_['weatherCondition']['rain'], fog=state_['weatherCondition']['fog'],
                                     wetness=state_['weatherCondition']['wetness'])
    sim.set_time_of_day(state_['weatherCondition']['time'])

    for agent in sim.get_agents():
        if agent.uid not in state_.keys():
            sim.remove_agent(agent)
            continue
        agent_state = state_[agent.uid]
        position = lgsvl.Vector(float(agent_state['positionX']), float(agent_state['positionY']),
                                float(agent_state['positionZ']))
        rotation = lgsvl.Vector(float(agent_state['rotationX']), float(agent_state['rotationY']),
                                float(agent_state['rotationZ']))
        velocity = lgsvl.Vector(float(agent_state['velocityX']), float(agent_state['velocityY']),
                                float(agent_state['velocityZ']))
        angular_velocity = lgsvl.Vector(float(agent_state['angularVelocityX']), float(agent_state['angularVelocityY']),
                                        float(agent_state['angularVelocityZ']))
        state = lgsvl.AgentState()
        state.transform.position = position
        state.transform.rotation = rotation
        state.velocity = velocity
        state.angular_velocity = angular_velocity
        agent.state = state

    return 'rollback'


@app.route(prefix + '/continue', methods=['POST'])
def continue_state():
    state_ID = str(request.args.get('ID'))
    state = open('state/current_state_{}.json'.format(state_ID), 'r')
    content = state.read()
    state_ = json.loads(content)
    sim.weather = lgsvl.WeatherState(rain=state_['weatherCondition']['rain'], fog=state_['weatherCondition']['fog'],
                                     wetness=state_['weatherCondition']['wetness'])
    sim.set_time_of_day(state_['weatherCondition']['time'])

    count = 0
    for key in state_.keys():
        if key == 'weatherCondition':
            continue
        agent_state = state_[key]
        position = lgsvl.Vector(float(agent_state['positionX']), float(agent_state['positionY']),
                                float(agent_state['positionZ']))
        rotation = lgsvl.Vector(float(agent_state['rotationX']), float(agent_state['rotationY']),
                                float(agent_state['rotationZ']))
        velocity = lgsvl.Vector(float(agent_state['velocityX']), float(agent_state['velocityY']),
                                float(agent_state['velocityZ']))
        angular_velocity = lgsvl.Vector(float(agent_state['angularVelocityX']), float(agent_state['angularVelocityY']),
                                        float(agent_state['angularVelocityZ']))
        state = lgsvl.AgentState()
        state.transform.position = position
        state.transform.rotation = rotation
        state.velocity = velocity
        state.angular_velocity = angular_velocity
        if count == 0:
            EGO.state = state
        else:
            obj_color = agent_state['obj_color'].split('(')[1].split(')')[0].split(',')
            sim.add_agent(agent_state['model'], lgsvl.AgentType.NPC, state,
                          lgsvl.Vector(obj_color[0], obj_color[1], obj_color[2]))

    return 'continue_state'


@app.route(prefix + 'weather/rain', methods=['POST'])
def set_rain():
    rain_level = float(request.args.get('rainLevel'))
    fog_level = sim.weather.fog
    cloudiness_level = sim.weather.cloudiness
    damage_level = sim.weather.damage

    sim.weather = lgsvl.WeatherState(rain=rain_level, fog=fog_level, wetness=rain_level, cloudiness=cloudiness_level,
                                     damage=damage_level)
    agents = sim.get_agents()
    ego = agents[0]
    return calculate_measures(agents, ego)


@app.route(prefix + 'weather/fog', methods=['POST'])
def set_fog():
    fog_level = float(request.args.get('fogLevel'))
    rain_level = sim.weather.rain
    cloudiness_level = sim.weather.cloudiness
    damage_level = sim.weather.damage

    sim.weather = lgsvl.WeatherState(rain=rain_level, fog=fog_level, wetness=rain_level, cloudiness=cloudiness_level,
                                     damage=damage_level)
    agents = sim.get_agents()
    ego = agents[0]
    return calculate_measures(agents, ego)


@app.route(prefix + 'weather/wetness', methods=['POST'])
def set_wetness():
    wetness_level = float(request.args.get('wetnessLevel'))
    fog_level = sim.weather.fog
    rain_level = sim.weather.rain
    cloudiness_level = sim.weather.cloudiness
    damage_level = sim.weather.damage

    sim.weather = lgsvl.WeatherState(rain=rain_level, fog=fog_level, wetness=wetness_level, cloudiness=cloudiness_level,
                                     damage=damage_level)
    agents = sim.get_agents()
    ego = agents[0]
    return calculate_measures(agents, ego)


@app.route(prefix + 'weather/cloudiness', methods=['POST'])
def set_cloudiness():
    cloudiness_level = float(request.args.get('cloudinessLevel'))
    wetness_level = sim.weather.wetness
    fog_level = sim.weather.fog
    rain_level = sim.weather.rain
    damage_level = sim.weather.damage
    sim.weather = lgsvl.WeatherState(rain=rain_level, fog=fog_level, wetness=wetness_level, cloudiness=cloudiness_level,
                                     damage=damage_level)

    agents = sim.get_agents()
    ego = agents[0]
    return calculate_measures(agents, ego)


@app.route(prefix + 'weather/damage', methods=['POST'])
def set_damage():
    damage_level = float(request.args.get('damageLevel'))
    cloudiness_level = sim.weather.cloudiness
    wetness_level = sim.weather.wetness
    fog_level = sim.weather.fog
    rain_level = sim.weather.rain
    sim.weather = lgsvl.WeatherState(rain=rain_level, fog=fog_level, wetness=wetness_level, cloudiness=cloudiness_level,
                                     damage=damage_level)
    agents = sim.get_agents()
    ego = agents[0]
    return calculate_measures(agents, ego)


@app.route(prefix + 'weather/nice', methods=['POST'])
def set_nice_weather():
    sim.weather = lgsvl.WeatherState(rain=0, fog=0, wetness=0, cloudiness=0, damage=0)
    agents = sim.get_agents()
    ego = agents[0]
    return calculate_measures(agents, ego)


@app.route(prefix + 'timeofday', methods=['POST'])
def set_time_of_day():
    t = float(request.args.get('time'))
    sim.set_time_of_day(t, fixed=False)
    agents = sim.get_agents()
    ego = agents[0]
    return calculate_measures(agents, ego)


@app.route(prefix + 'npc/vehicle/randomly', methods=['POST'])
def load_npc_vehicle_randomly():
    sim.add_random_agents(lgsvl.AgentType.NPC)
    agents = sim.get_agents()
    ego = agents[0]
    return calculate_measures(agents, ego)


@app.route(prefix + 'controllable/cone', methods=['POST'])
def add_cone():
    global CONE
    ego_transform = sim.get_agents()[0].state.transform
    forward = lgsvl.utils.transform_to_forward(ego_transform)

    state = lgsvl.ObjectState()
    state.transform.position = ego_transform.position + 50.0 * forward
    state.transform.rotation = ego_transform.rotation
    cone = sim.controllable_add("TrafficCone", state)
    CONE.append(cone)

    agents = sim.get_agents()
    ego = agents[0]
    return calculate_measures(agents, ego)


@app.route(prefix + 'agents/npc-vehicle/cross-road', methods=['POST'])
def add_npc_cross_road():
    global NPC_QUEUE
    which_car = str(request.args.get('car'))
    color = str(request.args.get('color'))
    change_lane = int(request.args.get('maintainlane'))
    distance = str(request.args.get('position'))
    colorV = set_color(color)

    ego_transform = sim.get_agents()[0].state.transform
    sx = ego_transform.position.x
    sy = ego_transform.position.y
    sz = ego_transform.position.z

    angle = math.pi
    dist = 20 if distance == 'near' else 50

    point = lgsvl.Vector(sx + dist * math.cos(angle), sy, sz + dist * math.sin(angle))
    state = lgsvl.AgentState()
    state.transform = sim.map_point_on_lane(point)

    generate = get_no_conflict_position(state.position, which_car)
    if generate:
        npc = sim.add_agent(which_car, lgsvl.AgentType.NPC, state, colorV)
        npc.follow_closest_lane(True, 20)
        npc.change_lane(change_lane == 1)

        control_agents_density(npc)
    agents = sim.get_agents()
    ego = agents[0]
    return calculate_measures(agents, ego)


@app.route(prefix + 'agents/pedestrian/cross-road', methods=['POST'])
def add_pedestrian_cross_road():
    global NPC_QUEUE
    direction = request.args.get('direction')
    ego_transform = sim.get_agents()[0].state.transform
    forward = lgsvl.utils.transform_to_forward(ego_transform)
    right = lgsvl.utils.transform_to_right(ego_transform)
    npc_state = lgsvl.AgentState()

    if direction == 'left':
        offset = - 5.0 * right
    else:
        offset = 5.0 * right

    wp = [lgsvl.WalkWaypoint(sim.map_point_on_lane(ego_transform.position + offset + 30 * forward).position, 1),
          lgsvl.WalkWaypoint(sim.map_point_on_lane(ego_transform.position - offset + 30 * forward).position, 1)]

    npc_state.transform.position = sim.map_point_on_lane(ego_transform.position + offset + 30.0 * forward).position

    generate = get_no_conflict_position(npc_state.transform.position, 'pedestrian')
    if generate:
        name = pedestrian[random.randint(0, 8)]
        p = sim.add_agent(name, lgsvl.AgentType.PEDESTRIAN, npc_state)
        p.follow(wp, loop=False)

        control_agents_density(p)

    agents = sim.get_agents()
    ego = agents[0]
    cp_list = calculate_measures(agents, ego)
    return cp_list


@app.route(prefix + 'agents/npc-vehicle/drive-ahead', methods=['POST'])
def add_npc_drive_ahead():
    global NPC_QUEUE
    which_lane = request.args.get('lane')
    which_car = str(request.args.get('car'))
    color = str(request.args.get('color'))
    change_lane = int(request.args.get('maintainlane'))
    distance = str(request.args.get('position'))
    colorV = set_color(color)

    ego_transform = sim.get_agents()[0].state.transform
    forward = lgsvl.utils.transform_to_forward(ego_transform)
    right = lgsvl.utils.transform_to_right(ego_transform)

    if distance == 'near':
        offset = 10
        if which_car == 'BoxTruck' or which_car == 'SchoolBus':
            forward = 15 * forward
            right = 4 * right
            speed = 10
        else:
            forward = 12 * forward
            right = 4 * right
            speed = 10
    else:
        offset = 50
        if which_car == 'BoxTruck' or which_car == 'SchoolBus':
            forward = 50 * forward
            right = 4 * right
            speed = 10
        else:
            forward = 50 * forward
            right = 4 * right
            speed = 10

    if which_lane == "left":
        point = ego_transform.position - right + forward
    elif which_lane == "right":
        point = ego_transform.position + right + forward
    elif which_lane == "current":
        point = ego_transform.position + forward
    else:
        point = lgsvl.Vector(ego_transform.position.x + offset * math.cos(0), ego_transform.position.y,
                             ego_transform.position.z + offset * math.sin(0))

    npc_state = lgsvl.AgentState()
    npc_state.transform = sim.map_point_on_lane(point)

    generate = get_no_conflict_position(npc_state.position, which_car)
    if generate:
        npc = sim.add_agent(which_car, lgsvl.AgentType.NPC, npc_state, colorV)
        npc.follow_closest_lane(True, speed)
        npc.change_lane(change_lane == 1)

        control_agents_density(npc)

    agents = sim.get_agents()
    ego = agents[0]
    return calculate_measures(agents, ego)


@app.route(prefix + 'agents/npc-vehicle/overtake', methods=['POST'])
def add_npc_overtake():
    global NPC_QUEUE
    which_lane = request.args.get('lane')
    which_car = str(request.args.get('car'))
    color = str(request.args.get('color'))
    change_lane = int(request.args.get('maintainlane'))
    distance = str(request.args.get('position'))
    colorV = set_color(color)

    ego_transform = sim.get_agents()[0].state.transform

    forward = lgsvl.utils.transform_to_forward(ego_transform)
    right = lgsvl.utils.transform_to_right(ego_transform)

    if distance == 'near':
        offset = 10
        if which_car == 'BoxTruck' or which_car == 'SchoolBus':
            forward = 20 * forward
            right = 5 * right
            speed = 20
        else:
            forward = 10 * forward
            right = 4 * right
            speed = 30
    else:
        offset = 50
        if which_car == 'BoxTruck' or which_car == 'SchoolBus':
            forward = 50 * forward
            right = 5 * right
            speed = 20
        else:
            forward = 50 * forward
            right = 4 * right
            speed = 30

    if which_lane == "left":
        point = ego_transform.position - right - forward
    elif which_lane == "right":
        point = ego_transform.position + right - forward
    elif which_lane == "current":
        point = ego_transform.position - forward
    else:
        point = lgsvl.Vector(ego_transform.position.x + offset * math.cos(0), ego_transform.position.y,
                             ego_transform.position.z + offset * math.sin(0))

    npc_state = lgsvl.AgentState()
    npc_state.transform = sim.map_point_on_lane(point)

    generate = get_no_conflict_position(npc_state.position, which_car)
    if generate:
        npc = sim.add_agent(which_car, lgsvl.AgentType.NPC, npc_state, colorV)
        npc.follow_closest_lane(True, speed)
        npc.change_lane(change_lane == 1)

        control_agents_density(npc)

    agents = sim.get_agents()
    ego = agents[0]
    return calculate_measures(agents, ego)


@app.route(prefix + 'agents/npc-vehicle/drive-opposite', methods=['POST'])
def add_npc_drive_opposite():
    global NPC_QUEUE
    which_car = str(request.args.get('car'))
    color = str(request.args.get('color'))
    change_lane = int(request.args.get('maintainlane'))
    distance = str(request.args.get('position'))
    colorV = set_color(color)

    ego_transform = sim.get_agents()[0].state.transform
    forward = lgsvl.utils.transform_to_forward(ego_transform)
    right = lgsvl.utils.transform_to_right(ego_transform)

    if distance == 'near':
        offset = 20
    else:
        offset = 50

    if which_car == 'BoxTruck' or which_car == 'SchoolBus':
        forward = offset * forward
        right = 8 * right
        speed = 20
    else:
        forward = offset * forward
        right = 8 * right
        speed = 20

    point = ego_transform.position - right + forward

    npc_state = lgsvl.AgentState()
    npc_state.transform = sim.map_point_on_lane(point)

    generate = get_no_conflict_position(npc_state.position, which_car)
    if generate:
        npc = sim.add_agent(which_car, lgsvl.AgentType.NPC, npc_state, colorV)
        npc.follow_closest_lane(True, speed)
        npc.change_lane(change_lane == 1)

        control_agents_density(npc)

    agents = sim.get_agents()
    ego = agents[0]
    return calculate_measures(agents, ego)


"""
Status APIs
"""


@app.route(prefix + 'get-datetime', methods=['GET'])
def get_time_stamp():
    timeofday = round(sim.time_of_day)
    if timeofday == 24:
        timeofday = 0
    dt = sim.current_datetime
    dt = dt.replace(hour=timeofday, minute=0, second=0)
    return json.dumps(int(time.mktime(dt.timetuple())))


@app.route(prefix + 'agents/number', methods=['GET'])
def get_agent_number():
    agents = sim.get_agents()
    for agent in agents:
        print(agent.transform.position)
    return json.dumps(len(agents))


@app.route(prefix + 'sensor/camera', methods=['GET'])
def get_camera_image():
    sensor_name = 'Main Camera'
    tag = int(request.args.get('tag'))
    frames = int(request.args.get('frames'))
    experiment_tag = str(request.args.get('experiment'))
    for i in range(frames):
        ProcessImageUtil.save_image(sensor_name, str(i), tag, experiment_tag)
        time.sleep(0.05)

    return json.dumps(tag)


@app.route(prefix + 'sensor/lidar', methods=['GET'])
def get_lidar_data():
    tag = int(request.args.get('tag'))
    experiment_tag = str(request.args.get('experiment'))
    ProcessImageUtil.save_lidar(tag, experiment_tag)
    return json.dumps(tag)


@app.route(prefix + 'sensor/velocity', methods=['GET'])
def get_velocity():
    velocity = sim.get_agents()[0].state.velocity
    velocity_dict = {'x': velocity.x, 'y': velocity.y, 'z': velocity.z}

    return json.dumps(velocity_dict)


@app.route(prefix + 'ego/ego-arrived', methods=['GET'])
def judge_arrived():
    position = sim.get_agents()[0].state.position
    if abs(position.x - DESTINATION[0]) < 5 and abs(position.z - DESTINATION[2]) < 6:
        return json.dumps('True')
    else:
        return json.dumps('False')


@app.route(prefix + 'sensor/speed', methods=['GET'])
def get_speed():
    speed = sim.get_agents()[0].state.speed
    return json.dumps(speed)


@app.route(prefix + 'ego/position', methods=['GET'])
def get_ego_position():
    position = sim.get_agents()[0].state.position
    pos_dict = {'x': position.x, 'y': position.y, 'z': position.z}
    return json.dumps(pos_dict)


@app.route(prefix + 'ego/collision_info', methods=['GET'])
def get_collision_info():
    global collision_object
    global collision_speed
    global JERK

    collision_info = str(collision_object)
    collision_speed_ = collision_speed

    collision_object = None
    collision_speed = 0
    JERK = 0
    collision_type = 'None'
    if collision_info == 'OBSTACLE':
        collision_type = "obstacle"
    if collision_info in npc_vehicle:
        collision_type = "npc_vehicle"
    if collision_info in pedestrian:
        collision_type = "pedestrian"
    return collision_type, collision_speed_


@app.route(prefix + 'ego/collision-probability', methods=['GET'])
def get_c_probability():
    global probability
    c_probability = probability
    probability = 0
    return str(c_probability)


if __name__ == '__main__':
    app.run(host='localhost', debug=False)
