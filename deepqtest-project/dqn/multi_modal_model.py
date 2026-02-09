# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/17 20:24
# @Author  : Chengjie
# @File    : multi_modal_model.py


import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import random
import math
from dqn.replay_memory import ReplayMemory

HyperParameter = dict(BATCH_SIZE=48, GAMMA=0.9, EPS_START=1, EPS_END=0.02, EPS_DECAY=6000, TARGET_UPDATE=100,
                      lr=1e-4, INITIAL_MEMORY=2000, MEMORY_SIZE=2000)

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
print('training with {}'.format(device))


class Multi_Modal_Model(nn.Module):
    def __init__(self, image_height, image_width, bird_height, bird_width, outputs):
        super(Multi_Modal_Model, self).__init__()

        # Number of Linear input connections depends on output of conv2d layers
        # and therefore the input image size, so compute it.
        def conv2d_size_out(size, kernel_size=3, stride=2):
            return (size - (kernel_size - 1) - 1) // stride + 2

        # CNN for the image feature extraction
        self.image_conv1 = nn.Conv2d(3, 32, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1))
        self.image_bn1 = nn.BatchNorm2d(32)
        self.image_conv2 = nn.Conv2d(32, 64, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1))
        self.image_bn2 = nn.BatchNorm2d(64)
        self.image_conv3 = nn.Conv2d(64, 128, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1))
        self.image_bn3 = nn.BatchNorm2d(128)
        self.image_conv4 = nn.Conv2d(128, 256, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1))
        self.image_bn4 = nn.BatchNorm2d(256)

        convImageWidth = conv2d_size_out(conv2d_size_out(conv2d_size_out(conv2d_size_out(image_width))))
        convImageHeight = conv2d_size_out(conv2d_size_out(conv2d_size_out(conv2d_size_out(image_height))))
        linear_image_input_size = convImageWidth * convImageHeight * 256
        self.image_fc5 = nn.Linear(linear_image_input_size, 256)
        self.image_out = nn.Linear(256, 128)

        # CNN for the bird view feature extraction
        self.bird_conv1 = nn.Conv2d(15, 32, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1))
        self.bird_bn1 = nn.BatchNorm2d(32)
        self.bird_conv2 = nn.Conv2d(32, 64, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1))
        self.bird_bn2 = nn.BatchNorm2d(64)
        self.bird_conv3 = nn.Conv2d(64, 128, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1))
        self.bird_bn3 = nn.BatchNorm2d(128)
        self.bird_conv4 = nn.Conv2d(128, 256, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1))
        self.bird_bn4 = nn.BatchNorm2d(256)

        convBirdWidth = conv2d_size_out(conv2d_size_out(conv2d_size_out(conv2d_size_out(bird_width))))
        convBirdHeight = conv2d_size_out(conv2d_size_out(conv2d_size_out(conv2d_size_out(bird_height))))
        linear_bird_input_size = convBirdWidth * convBirdHeight * 256
        self.bird_fc5 = nn.Linear(linear_bird_input_size, 256)
        self.bird_out = nn.Linear(256, 512)

        self.dnn_fc1 = nn.Linear(1, 200)
        self.dnn_fc1.weight.data.normal_(0, 0.1)  # initialization
        self.dnn_fc2 = nn.Linear(200, 200)
        self.dnn_fc2.weight.data.normal_(0, 0.1)  # initialization
        self.dnn_out = nn.Linear(200, 64)
        self.dnn_out.weight.data.normal_(0, 0.1)  # initialization

        self.lstm = nn.LSTM(704, 64, 2, batch_first=True)
        self.dropout = nn.Dropout(0.1)
        self.lstm_fc = nn.Linear(64, outputs)

    def forward(self, image, bird, speed):
        image = image.float() / 255
        # print(image.shape)
        image_ = F.relu(self.image_bn1(self.image_conv1(image)))
        image_ = F.relu(self.image_bn2(self.image_conv2(image_)))
        image_ = F.relu(self.image_bn3(self.image_conv3(image_)))
        image_ = F.relu(self.image_bn4(self.image_conv4(image_)))
        image_ = F.relu(self.image_fc5(image_.view(image_.size()[0], -1)))
        image_out = F.relu(self.image_out(image_))

        bird = bird.float() / 255
        bird_ = F.relu(self.bird_bn1(self.bird_conv1(bird)))
        bird_ = F.relu(self.bird_bn2(self.bird_conv2(bird_)))
        bird_ = F.relu(self.bird_bn3(self.bird_conv3(bird_)))
        bird_ = F.relu(self.bird_bn4(self.bird_conv4(bird_)))
        bird_ = F.relu(self.bird_fc5(bird_.view(bird_.size()[0], -1)))
        bird_out = F.relu(self.bird_out(bird_))

        speed = speed.float() / 255
        speed_ = F.relu(self.dnn_fc1(speed))
        speed_ = F.relu(self.dnn_fc2(speed_))
        speed_out = F.relu(self.dnn_out(speed_))

        # combine all the feature
        # print('shape: ', image_out.shape, bird_out.shape, speed_out.shape)
        combine_fea = torch.cat((image_out, bird_out, speed_out), 1)
        combine_fea = combine_fea.unsqueeze(0)
        # print(combine_fea.shape)
        lstm_out, _ = self.lstm(combine_fea)
        lstm_out = self.dropout(lstm_out[:, -1])
        lstm_out = F.relu(self.lstm_fc(lstm_out))
        return lstm_out


class DQN(object):
    def __init__(self, image_height, image_width, bird_height, bird_width, outputs):
        self.eval_net, self.target_net = Multi_Modal_Model(image_height, image_width, bird_height, bird_width, outputs), \
                                         Multi_Modal_Model(image_height, image_width, bird_height, bird_width, outputs)

        self.eval_net.cuda()
        self.target_net.cuda()

        self.memory = ReplayMemory(HyperParameter['MEMORY_SIZE'])
        # setup optimizer
        self.steps_done = 0
        self.optimizer = optim.Adam(self.eval_net.parameters(), lr=HyperParameter['lr'], weight_decay=1e-5)
        self.device = device
        self.N_ACTION = outputs

    def select_action(self, image, bird, speed):
        """
        Select action.
        :param speed:
        :param image:
        :param bird:
        :return:
        """
        # global steps_done
        sample = random.random()
        eps_threshold = HyperParameter['EPS_END'] + (
                HyperParameter['EPS_START'] - HyperParameter['EPS_END']) * math.exp(
            -1. * self.steps_done / HyperParameter['EPS_DECAY'])
        self.steps_done += 1
        if sample > eps_threshold:
            with torch.no_grad():
                return self.eval_net(image, bird, speed).max(1)[1].view(1, 1), self.steps_done
        else:
            return torch.tensor([[random.randrange(self.N_ACTION)]], device=device, dtype=torch.long), self.steps_done

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

        no_final_mask = torch.tensor(tuple(map(lambda s: s is not None, batch.next_speed)), device=device,
                                     dtype=torch.bool)
        non_final_next_image = torch.cat([s for s in batch.next_image if s is not None]).to(device)
        non_final_next_bird = torch.cat([s for s in batch.next_bird if s is not None]).to(device)
        non_final_next_speed = torch.cat([s for s in batch.next_speed if s is not None]).to(device)

        # print(batch.state, batch.action, batch.reward)
        image_batch = torch.cat(batch.image).to(device)
        bird_batch = torch.cat(batch.bird).to(device)
        speed_batch = torch.cat(batch.speed).to(device)
        action_batch = torch.cat(actions).view(1, batch_size)
        reward_batch = torch.cat(reward)

        state_action_values = self.eval_net(image_batch, bird_batch, speed_batch).gather(1, action_batch)

        next_state_values = torch.zeros(HyperParameter['BATCH_SIZE'], device=device)
        next_state_values[no_final_mask] = self.eval_net(non_final_next_image, non_final_next_bird, non_final_next_speed).max(1)[0].detach()
        expected_state_action_values = (next_state_values * HyperParameter['GAMMA']) + reward_batch

        # print(state_action_values, expected_state_action_values.unsqueeze(0))

        loss = F.smooth_l1_loss(state_action_values, expected_state_action_values.unsqueeze(0))
        self.optimizer.zero_grad()
        loss.backward()
        for param in self.eval_net.parameters():
            param.grad.data.clamp_(-1, 1)
        self.optimizer.step()


if __name__ == '__main__':
    model = Multi_Modal_Model(160, 376, 300, 300, 78).to(device)
    print(model)
