# ---------------------- CODE TAKEN FROM ----------------------
# https://www.geeksforgeeks.org/q-learning-in-python/
# ---------------------- CODE TAKEN FROM ----------------------

import gymnasium as gym
import math
import random
import matplotlib
import matplotlib.pyplot as plt
from collections import namedtuple, deque
from itertools import count
import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F


env = gym.make("CartPole-v1")

# set up matplotlib
is_ipython = 'inline' in matplotlib.get_backend()
if is_ipython:
    from IPython import display

plt.ion()

# if GPU is to be used
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    
# BATCH_SIZE is the number of transitions sampled from the replay buffer
# GAMMA is the discount factor as mentioned in the previous section
# EPS_START is the starting value of epsilon
# EPS_END is the final value of epsilon
# EPS_DECAY controls the rate of exponential decay of epsilon, higher means a slower decay
# TAU is the update rate of the target network
# LR is the learning rate of the ``AdamW`` optimizer
BATCH_SIZE = 128
GAMMA = 0.99
EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 5000
TAU = 0.005
LR = 1e-4

# Get number of actions from gym action space
n_actions = env.action_space.n
# Get the number of state observations
state, info = env.reset()
n_observations = len(state)

# Initialize Q-table with zeros
Q_table = np.zeros((n_observations, n_actions))

# Define Bellman equation parameters
learning_rate = 0.8
discount_factor = 0.95
epochs = 1000

steps_done = 0


def select_action(state, Q_table):
    global steps_done
    sample = random.random()
    eps_threshold = EPS_END + (EPS_START - EPS_END) * \
        math.exp(-1. * steps_done / EPS_DECAY)
    steps_done += 1

    if sample < eps_threshold:
        return np.random.randint(0, n_actions)  # Explore
    else:
        return np.argmax(Q_table[state])  # Exploit


episode_durations = []


def plot_durations(show_result=False):
    plt.figure(1)
    durations_t = torch.tensor(episode_durations, dtype=torch.float)
    if show_result:
        plt.title('Result')
    else:
        plt.clf()
        plt.title('Training...')
    plt.xlabel('Episode')
    plt.ylabel('Duration')
    plt.plot(durations_t.numpy())
    # Take 100 episode averages and plot them too
    if len(durations_t) >= 100:
        means = durations_t.unfold(0, 100, 1).mean(1).view(-1)
        means = torch.cat((torch.zeros(99), means))
        plt.plot(means.numpy())

    plt.pause(0.001)  # pause a bit so that plots are updated
    if is_ipython:
        if not show_result:
            display.display(plt.gcf())
            display.clear_output(wait=True)
            pass
        else:
            display.display(plt.gcf())


if torch.cuda.is_available():
    num_episodes = 600
else:
    num_episodes = 400

for i_episode in range(num_episodes):
    # Initialize the environment and get its state
    current_state, info = env.reset()
    print(env.observation_space.low)
    print(env.observation_space.high)
    
    for t in count():
        action = select_action(current_state, Q_table)
        observation, reward, terminated, truncated, _ = env.step(action)
        #env.render()

        done = terminated or truncated

        if terminated:
            next_state = None
        else:
            next_state = observation

        # Update Q-value using the Q-learning update rule
        Q_table[current_state, action] += learning_rate * \
            (reward + discount_factor *
             np.max(Q_table[next_state]) - Q_table[current_state, action])

        current_state = next_state  # Move to the next state

        if done:
            episode_durations.append(t + 1)
            plot_durations()
            break

print('Complete')
plot_durations(show_result=True)
plt.ioff()
plt.show()
