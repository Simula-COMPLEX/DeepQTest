import math
import numpy as np

pedestrian = [
    "Bob",
    "EntrepreneurFemale",
    "Howard",
    "Johny",
    "Pamela",
    "Presley",
    "Robin",
    "Stephen",
    "Zoe"
]

npc_vehicle = {
    "Sedan",
    "SUV",
    "Jeep",
    "Hatchback",
    "SchoolBus",
    "BoxTruck"
}


def calculate_angle(vector1, vector2):
    cos_theta = (vector1.x * vector2.x + vector1.y * vector2.y + vector1.z * vector2.z) / \
                ((math.sqrt(vector1.x * vector1.x + vector1.y * vector1.y + vector1.z * vector1.z) *
                  math.sqrt(vector2.x * vector2.x + vector2.y * vector2.y + vector2.z * vector2.z)))
    theta = np.arccos(cos_theta)
    return theta


def get_line(agent):
    agent_position_x = agent.transform.position.x
    agent_position_z = agent.transform.position.z

    agent_velocity_x = agent.state.velocity.x if agent.state.velocity.x != 0 else 0.0001
    agent_velocity_z = agent.state.velocity.z

    return agent_velocity_z / agent_velocity_x, -(
            agent_velocity_z / agent_velocity_x) * agent_position_x + agent_position_z


def get_distance(agent, x, z):
    return math.sqrt(pow(agent.transform.position.x - x, 2) + pow(agent.transform.position.z - z, 2))


def judge_same_line(agent1, agent2, k1, k2):
    judge = False
    direction_vector = (agent1.transform.position.x - agent2.transform.position.x,
                        agent1.transform.position.z - agent2.transform.position.z)
    distance = get_distance(agent1, agent2.transform.position.x, agent2.transform.position.z)

    if abs(k1 - k2) < 0.5:
        if abs((agent1.transform.position.z - agent2.transform.position.z) /
               ((agent1.transform.position.x - agent2.transform.position.x) if (
                                                                                       agent1.transform.position.x - agent2.transform.position.x) != 0 else 0.01) - (
                       k1 + k2) / 2) < 0.6:
            judge = True

    if not judge:
        return judge, -1

    if direction_vector[0] * agent1.state.velocity.x >= 0 and direction_vector[1] * agent1.state.velocity.z >= 0:
        TTC = distance / (agent1.state.speed - agent2.state.speed)
    else:
        TTC = distance / (agent2.state.speed - agent1.state.speed)
    if TTC < 0:
        TTC = 100000

    return judge, TTC


def calculate_TTC(agents, ego, ttc_calcu):
    if ttc_calcu:
        trajectory_ego_k, trajectory_ego_b = get_line(ego)
        ego_speed = ego.state.speed if ego.state.speed > 0.01 else 0.01

    TTC = 100000
    distance = 100000

    for i in range(1, len(agents)):
        dis = get_distance(ego, agents[i].transform.position.x, agents[i].transform.position.z)
        distance = dis if dis <= distance else distance

        if ttc_calcu:
            trajectory_agent_k, trajectory_agent_b = get_line(agents[i])
            agent_speed = agents[i].state.speed if agents[i].state.speed > 0.01 else 0.01

            same_lane, ttc = judge_same_line(ego, agents[i], trajectory_ego_k, trajectory_agent_k)
            if same_lane:
                continue
            else:
                trajectory_agent_k = trajectory_agent_k if trajectory_ego_k - trajectory_agent_k != 0 else trajectory_agent_k + 0.0001

                collision_point_x, collision_point_z = (trajectory_agent_b - trajectory_ego_b) / (
                        trajectory_ego_k - trajectory_agent_k), \
                                                       (
                                                               trajectory_ego_k * trajectory_agent_b - trajectory_agent_k * trajectory_ego_b) / (
                                                               trajectory_ego_k - trajectory_agent_k)

                ego_distance = get_distance(ego, collision_point_x, collision_point_z)
                agent_distance = get_distance(agents[i], collision_point_x, collision_point_z)
                time_ego = ego_distance / ego_speed
                time_agent = agent_distance / agent_speed
                if ego_speed == 0.01 and agent_speed == 0.01:
                    TTC = min(TTC, 100000)
                else:
                    if abs(time_ego - time_agent) < 1:
                        TTC = min(TTC, (time_ego + time_agent) / 2)

    return TTC, distance
