# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/4/15 17:32
# @Author  : Chengjie
# @File    : model.py

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import random
import math
from dqn.replay_memory import ReplayMemory, Transition

# HyperParameter = dict(BATCH_SIZE=32, GAMMA=0.99, EPS_START=1, EPS_END=0.02, EPS_DECAY=1000000, TARGET_UPDATE=1000,
#                       lr=1e-4, INITIAL_MEMORY=10000, MEMORY_SIZE=10 * 10000)
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
HyperParameter = dict(BATCH_SIZE=128, GAMMA=0.9, EPS_START=1, EPS_END=0.02, EPS_DECAY=5000, TARGET_UPDATE=50,
                      lr=1e-4, INITIAL_MEMORY=1000, MEMORY_SIZE=1000)

device = torch.device("cpu")


class CNN(nn.Module):
    def __init__(self, height, width, outputs):
        super(CNN, self).__init__()
        self.conv1 = nn.Conv2d(4, 32, kernel_size=3, stride=2, padding=1)
        self.max_pool1 = nn.MaxPool2d(2)
        self.bn1 = nn.BatchNorm2d(32)  # 在卷积神经网络的卷积层之后总会添加BatchNorm2d进行数据的归一化处理，这使得数据在进行Relu之前不会因为数据过大而导致网络性能的不稳定.
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1)
        self.bn4 = nn.BatchNorm2d(256)

        # Number of Linear input connections depends on output of conv2d layers
        # and therefore the input image size, so compute it.
        def conv2d_size_out(size, kernel_size=3, stride=2):
            return (size - (kernel_size - 1) - 1) // stride + 2

        convWidth = conv2d_size_out(conv2d_size_out(conv2d_size_out(conv2d_size_out(width))))
        convHeight = conv2d_size_out(conv2d_size_out(conv2d_size_out(conv2d_size_out(height))))
        linear_input_size = convWidth * convHeight * 256
        self.fc5 = nn.Linear(linear_input_size, 256)
        self.head = nn.Linear(256, outputs)

    def forward(self, x):
        x = x.float() / 255
        x1 = F.relu(self.bn1(self.conv1(x)))
        x2 = F.relu(self.bn2(self.conv2(x1)))
        x3 = F.relu(self.bn3(self.conv3(x2)))
        x4 = F.relu(self.bn4(self.conv4(x3)))
        x5 = F.relu(self.fc5(x4.view(x4.size()[0], -1)))
        return self.head(x5)


steps_done = 0


class DQN(object):
    def __init__(self, height, width, outputs):
        """
        Initialize the dqn model.
        :param height: height of the input
        :param width: width of the input
        :param outputs: action space size
        """
        self.eval_net, self.target_net = CNN(height, width, outputs), CNN(height, width, outputs)
        self.memory = ReplayMemory(HyperParameter['MEMORY_SIZE'])
        # Setup optimizer
        self.optimizer = optim.Adam(self.eval_net.parameters(), HyperParameter['lr'])
        self.device = device
        self.N_ACTION = outputs

    def select_action(self, state):
        """
        Select action.
        :param state:
        :return:
        """
        global steps_done
        sample = random.random()
        eps_threshold = HyperParameter['EPS_END'] + (
                HyperParameter['EPS_START'] - HyperParameter['EPS_END']) * math.exp(
            -1. * steps_done / HyperParameter['EPS_DECAY'])
        steps_done += 1
        if sample > eps_threshold:
            with torch.no_grad():
                return self.eval_net(state.to(device)).max(1)[1].view(1, 1), steps_done
        else:
            return torch.tensor([[random.randrange(self.N_ACTION)]], device=device, dtype=torch.long), steps_done

    def optimize_model(self):
        """
        Model optimization.
        :return:
        """
        batch_size = HyperParameter['BATCH_SIZE']
        if len(self.memory) < batch_size:
            return

        batch = self.memory.sample(batch_size)

        # map: https://www.runoob.com/python/python-func-map.html
        # a = torch.tensor([[batch.action]])
        #####
        # lambda
        # map(lambda a: torch.tensor([[a]], device='cuda'), batch.action) equals to
        # --- x = lambda r: torch.tensor([[r]], device='cuda')
        # --- print(x(batch.action))

        ####
        # tuple: https://www.runoob.com/python/att-tuple-tuple.html
        # actions = tuple((map(lambda a: torch.tensor([[a]], device='cuda'), batch.action)))
        # reward = tuple((map(lambda r: torch.tensor([r], device='cuda'), batch.reward)))
        actions = tuple((map(lambda a: torch.tensor([[a]], device=device), batch.action)))
        reward = tuple((map(lambda r: torch.tensor([r], device=device, dtype=torch.float), batch.reward)))

        no_final_mask = torch.tensor(tuple(map(lambda s: s is not None, batch.next_state)), device=device, dtype=torch.bool)
        print(no_final_mask)
        non_final_next_states = torch.cat([s for s in batch.next_state if s is not None]).to(device)

        # print(batch.state, batch.action, batch.reward)
        state_batch = torch.cat(batch.state).to(device)
        action_batch = torch.cat(actions)
        reward_batch = torch.cat(reward)

        state_action_values = self.eval_net(state_batch).gather(1, action_batch)

        next_state_values = torch.zeros(HyperParameter['BATCH_SIZE'], device=device)
        next_state_values[no_final_mask] = self.eval_net(non_final_next_states).max(1)[0].detach()
        expected_state_action_values = (next_state_values * HyperParameter['GAMMA']) + reward_batch

        loss = F.smooth_l1_loss(state_action_values, expected_state_action_values.unsqueeze(1))
        self.optimizer.zero_grad()
        loss.backward()
        for param in self.eval_net.parameters():
            param.grad.data.clamp_(-1, 1)
        self.optimizer.step()


