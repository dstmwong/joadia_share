# -*- coding: utf-8 -*-
"""
Created on Tue Feb 12 13:15:40 2019

@author: wongm
"""

import gym
import gym.spaces
env = gym.make("joadia-v0")

#from IPython import display
#import matplotlib.pyplot as plt
#
env.reset()
#
#img = plt.imshow(env.render(mode='rgb_array'))
#for _ in range(100):
#    img.set_data(env.render(mode='rgb_array'))
#    display.display(plt.gcf())
#    display.clear_output(wait=True)
#    action=env.action_space.sample()
#    env.step(action)

