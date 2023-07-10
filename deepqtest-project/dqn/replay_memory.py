# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/4/15 17:32
# @Author  : Chengjie
# @File    : replay-memory.py


from collections import namedtuple
import random

Transition = namedtuple('Transition', ('image', 'bird', 'speed', 'action', 'next_image', 'next_bird', 'next_speed', 'reward'))


#  Replay memory (Experience Pool)
class ReplayMemory(object):
    def __init__(self, capacity):
        """
        Initialize the replay memory
        :param capacity: HyperParameter which is memory size
        """
        self.capacity = capacity
        self.total_steps = 0
        self.memory = []
        self.position = 0

    def push(self, *args):
        """
        Push new transition into replay memory.
        :param args: new transition
        :return:
        """
        self.total_steps += 1
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = Transition(*args)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        """
        Random select batch_size transitions from memory.
        :param batch_size: HyperParameter
        :return: The sampled memories which are used for network training.
        """
        transitions = random.sample(self.memory, batch_size)
        return Transition(*zip(*transitions))

    def __len__(self):
        """
        :return: The current length of memory.
        """
        return len(self.memory)
