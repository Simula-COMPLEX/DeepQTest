# DeepQTest: Testing Autonomous Driving Systems with Reinforcement Learning and Real-world Weather Data

> To facilitate reviewing our proposed approach, reviewers please refer to the corresponding data in this repository.<br/>

This repository contains:

1. **[deepqtest-project](https://github.com/Simula-COMPLEX/DeepQTest/tree/main/deepqtest-project)** - all related algorithms and source code for conducting the experiment;
2. **[formal-experiment](https://github.com/Simula-COMPLEX/DeepQTest/tree/main/formal-experiment)** - all the raw data for the experiment results and analyses;
3. **[rest-api](https://github.com/Simula-COMPLEX/DeepQTest/tree/main/rest-api)** - the list of REST API endpoints for configuring the environment.

## Description

Autonomous driving systems (ADSs) are safety-critical, and testing them is one of the important approaches to ensure their safety. However, due to the inherent complexity of ADSs and the high dimensionality of their operating environment, the operating environment of ADSs is dynamic, continuously evolving, and full of uncertainties, which requires a testing approach adaptive to the environment. In addition, existing ADS testing techniques have limited effectiveness in ensuring the realism of test scenarios, especially the realism of weather conditions and their changes over time. In this paper, we present DeepQTest, a novel ADS testing approach that uses Reinforcement Learning to learn environment configurations with a high chance of revealing abnormal ADS behaviors. Specifically, DeepQTest employs Deep Q-Learning and adopts three safety and comfort measures to construct the reward functions. To ensure the realism of generated scenarios, DeepQTest defines a set of realistic constraints and introduces real-world weather conditions into the simulated environment. We employed three comparison baselines, i.e., random, greedy, and a state-of-the-art RL-based approach DeepCollision, for evaluating DeepQTest on an industrial-scale ADS. Evaluation results show that DeepQTest demonstrated significantly better effectiveness in terms of generating scenarios leading to collisions and ensuring generated test scenario realism compared with the baselines.
 
## DeepQTest Overview

<div align=center><img src="https://github.com/Simula-COMPLEX/DeepQTest/blob/main/figures/overview.png" width="960" /></div>

## Prerequisite

- [SVL Simulator 2021.1](https://github.com/lgsvl/simulator/releases/tag/2021.1)
- [Apollo 5.0](https://github.com/ApolloAuto/apollo/releases/tag/v5.0.0)
- [SORA-SVL](https://github.com/YuqiHuai/SORA-SVL) Local cloud for SVL Simulator maintained by [Yuqi Huai](https://github.com/YuqiHuai). Unfortunately, SVL Simulator is no longer maintained by the official team, and the cloud has also been shut down by the official team.

## Usage Example

### Install the dependencies using *requirement.txt*
```sh
pip install -r requirements.txt
```

### Run the environment configuration API [script](https://github.com/Simula-COMPLEX/DeepQTest/blob/main/deepqtest-project/restapi/svlapis/environment_configuration_rest_apis.py), and use the following function to set up the testing environment

```python
def initialization(enable='True', simulationtime=3, date='2021-7-8', time='8:00:00', city='SanFrancisco', road_start='road1_start',
                   destination=(-300.34, 10.20, -14.54)):

    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/set-simulationtime?simulationtime={}".format(simulationtime))
    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/load-map?map={}&road_start={}".format('SanFrancisco', road_start))
    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/set-datetime?date={}&time={}".format(date, time))
    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/load-city-weather?city={}&date={}".format(city, date))

    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/connect-dreamview")
    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/enable-modules")
    requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/set-destination?des_x={}&des_y={}&des_z={}".format(destination[0], destination[1], destination[2]))
```

### Configure the environment by calling REST APIs

```python
requests.post("http://127.0.0.1:5000/deepqtest/lgsvl-api/agents/pedestrian/cross-road?direction=right")
```

## People

- Chengjie Lu https://www.simula.no/people/chengjielu
- Tao Yue https://www.simula.no/people/tao
- Man Zhang
- Shaukat Ali https://www.simula.no/people/shaukat
