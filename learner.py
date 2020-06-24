import random
import numpy as np
from tqdm import tqdm

def epsilon_greedy(Q, n_actions, epsilon):
    """
    Epsilon-greedy algorithm.
    @param Q game state representation table
    @param n_actions number of choices
    @param epsilon chance that greedy action isn't taken
    @return action
    """
    if np.random.rand() < epsilon:
        return np.random.randint(n_actions)
    else:
        amax, n_max = np.argmax(Q), n_actions - 1
        return amax if amax <= n_max else n_max

def decay(eps):
    """
    Epsilon decay. (min_bound ETA: 1,381,548 matches)
    @param eps epsilon value to decay
    @return decayed version of eps unless eps is too small
    """
    decay, min_bound = .999995, .001
    new_eps = eps * decay
    
    return new_eps if new_eps > min_bound else min_bound

class QLearner:
    def __init__(self, env, gamma=.9, alpha=.1, Q=None):
        self.env = env
        self.gamma, self.alpha = gamma, alpha
        self.n_states, self.n_actions = env.n_states, env.actions
        # self.strategy, self.step = self.init_strategy(), 0
        
        if Q is None:
            self.Q = np.zeros((self.n_states, self.n_actions))
        else:
            self.Q = Q

    def init_strategy(self):
        """
        Loads in list of starting strategies and chooses one
        @return random strategy
        """
        strats = np.loadtxt('strategies.txt', delimiter=',', dtype=int)
        return random.choice(strats)

    def learn(self, matches, epsilon=1., winners=None, policy=None, render=False, interval=1,):
        """
        Learns env game over the number of matches passed in. Env designed similar to Gym env.
        @param matches number of episodes
        @param epsilon value for e-greedy alg.
        @param winners map/dict containing number of wins for each player
        @param policy policy that determines actions
        @param render if True displays end game state
        @param interval frequency of rendering
        @return Q table after matches have been played, winners map/dict
        """
        winners = { 'None': 0 }
        p1, p2 = self.env.players

        if policy is None:
            policy = epsilon_greedy

        if winners is not None:
            for player in self.env.players:
                winners[player] = 0

        for match in tqdm(range(matches)):
            done, s = False, self.env.reset()

            while not done:
                actions = [
                    np.random.randint(self.n_actions), 
                    policy(Q=self.Q[s], n_actions=self.n_actions, epsilon=epsilon)
                ]
                rews, s_, actions, done, _ = self.env.step(actions)
                delta = rews[1] + self.gamma * self.Q[s_, np.argmax(self.Q[s_])]
                self.Q[s, actions[1]] = (1 - self.alpha) * self.Q[s, actions[1]] + self.alpha * delta
                s = s_

            epsilon = decay(epsilon)

            if winners is not None:
                winners[self.env.winner] += 1

            if render and match % interval == 0:
                self.env.render()

        print('Finished training...')
        return self.Q, winners, epsilon

    def play(self, epsilon=.001, policy=None):
        """
        Plays game vs AI where player moves first.
        @param epsilon value for e-greedy alg.
        @param policy policy that determines actions
        @return winner of match
        """
        if policy is None:
            policy = epsilon_greedy

        done, s = False, self.env.reset()

        self.env.render()
        while not done:
            actions = [
                int(input('Choose an action: [0-6]:')),
                policy(Q=self.Q[s], n_actions=self.n_actions, epsilon=epsilon)
            ]

            r_, s_, actions, done, _ = self.env.step(actions) 
            s = s_

            self.env.render()

        return self.env.winner

class DoubleQLearner:
    def __init__(self, env, gamma=.9, alpha=.1):
        self.env = env
        self.gamma, self.alpha = gamma, alpha
        self.n_states, self.n_actions = env.n_states, env.actions
        self.Q1 = np.zeros((self.n_states, self.n_actions))
        self.Q2 = np.zeros((self.n_states, self.n_actions))
        self.Qf = np.zeros((self.n_states, self.n_actions))

    def learn(self, matches, epsilon=1., winners=None, policy=None, render=False, interval=1,):
        """
        Learns env game over the number of matches passed in. Env designed similar to Gym env.
        @param matches number of episodes
        @param epsilon value for e-greedy alg.
        @param winners map/dict containing number of wins for each player
        @param policy policy that determines actions
        @param render if True displays end game state
        @param interval frequency of rendering
        @return Final Q table after matches have been played, winners map/dict
        """
        winners = { 'None': 0 }

        if policy is None:
            policy = epsilon_greedy

        if winners is not None:
            for player in self.env.players:
                winners[player] = 0

        for match in tqdm(range(matches)):
            done, s = False, self.env.reset()

            while not done:
                self.Qf = (self.Q1 + self.Q2) / 2.
                actions = [
                    policy(Q=self.Qf[s], n_actions=self.n_actions, epsilon=epsilon), 
                    policy(Q=self.Qf[s], n_actions=self.n_actions, epsilon=epsilon)
                ]
                rews, s_, actions, done, _ = self.env.step(actions)

                if np.random.rand() < .5:
                    delta = rews[0] + self.gamma * self.Q1[s_, np.argmax(self.Q2[s_])]
                    self.Q1[s, actions[0]] = (1 - self.alpha) * self.Q1[s, actions[0]] + self.alpha * delta
                else:
                    delta = rews[0] + self.gamma * self.Q2[s_, np.argmax(self.Q1[s_])]
                    self.Q2[s, actions[0]] = (1 - self.alpha) * self.Q2[s, actions[0]] + self.alpha * delta

                s = s_

            epsilon = decay(epsilon)

            if winners is not None:
                winners[self.env.winner] += 1

            if render and match % interval == 0:
                self.env.render()

        return self.Qf, winners
