# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/4/15 17:31
# @Author  : Chengjie
# @File    : test.py


from collections import namedtuple
import random
import torch

# Why Transition[*zip(*t)]
# https://www.cnblogs.com/52dxer/p/14139911.html
batch_size = 3
Transition = namedtuple('Transition', ('state', 'next_state', 'action', 'reward'))

a = Transition(state=1, next_state=2, action=3, reward=4)
b = Transition(state=11, next_state=12, action=13, reward=14)
c = Transition(state=21, next_state=22, action=23, reward=24)
d = Transition(state=31, next_state=32, action=33, reward=34)
e = Transition(state=41, next_state=42, action=43, reward=44)

f = [a, b, c, d]
t = random.sample(f, batch_size)
print(t)

# 将t进行解压操作
print(*zip(*t))

# 解压后再放入Transition
print(Transition(*zip(*t)))
print('-----')
batch = Transition(*zip(*t))
actions = tuple((map(lambda aa: torch.tensor([[aa]], device='cuda'), batch.action)))
reward = tuple((map(lambda r: torch.tensor([r], device='cuda'), batch.reward)))
print(reward)
print(actions)

# x = lambda r: torch.tensor([[r]], device='cuda')
# print(x(batch.action))
# print(torch.tensor([[batch.action]], device='cuda'))

torch.cat(actions)


import queue

queue1 = queue.Queue(maxsize=5)

queue1.put(1)
queue1.put(2)
queue1.put(3)
queue1.put(4)
queue1.put(5)

queue1.put(6)


print('test: ', queue1.get())

queue1.put(5)

while not queue1.empty():
    print(queue1.get())

print(queue1.qsize())
