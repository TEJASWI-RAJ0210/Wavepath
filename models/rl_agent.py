import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env


class MoodJourneyEnv(gym.Env):
    metadata = {'render_modes': []}

    def __init__(self, candidates: list, target: tuple):
        super().__init__()
        self.candidates  = candidates
        self.target_val  = target[0]
        self.target_nrg  = target[1]
        self.n           = len(candidates)
        self.action_space      = spaces.Discrete(self.n)
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(5,), dtype=np.float32
        )
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.cur_val    = self.candidates[0]['valence']
        self.cur_nrg    = self.candidates[0]['energy']
        self.step_count = 0
        self.used       = set()
        return self._obs(), {}

    def _obs(self):
        return np.array([
            self.cur_val, self.cur_nrg,
            self.target_val, self.target_nrg,
            self.step_count / max(self.n, 1)
        ], dtype=np.float32)

    def step(self, action: int):
        action = int(action)
        if action in self.used:
            action = next((i for i in range(self.n)
                           if i not in self.used), 0)
        self.used.add(action)
        song = self.candidates[action]

        p        = (self.step_count + 1) / self.n
        sv, se   = self.candidates[0]['valence'], self.candidates[0]['energy']
        ideal_val = sv + p * (self.target_val - sv)
        ideal_nrg = se + p * (self.target_nrg - se)

        reward = -(abs(song['valence'] - ideal_val) +
                   abs(song['energy']  - ideal_nrg))

        if ((song['valence'] - self.target_val) ** 2 +
            (song['energy']  - self.target_nrg) ** 2) ** 0.5 < 0.1:
            reward += 2.0

        self.cur_val     = song['valence']
        self.cur_nrg     = song['energy']
        self.step_count += 1
        done = self.step_count >= self.n
        return self._obs(), reward, done, False, {}


def train_rl_agent(candidates, target_mood,
                   timesteps=50_000,
                   save_path='models/ppo_mood_agent'):
    env = MoodJourneyEnv(candidates, target_mood)
    check_env(env, warn=True)
    model = PPO('MlpPolicy', env, verbose=1,
                learning_rate=3e-4, n_steps=512, batch_size=64)
    model.learn(total_timesteps=timesteps)
    model.save(save_path)
    print(f'Agent saved to {save_path}.zip')
    return model


def get_rl_ordered_playlist(candidates, target_mood,
                             model_path='models/ppo_mood_agent'):
    model   = PPO.load(model_path)
    env     = MoodJourneyEnv(candidates, target_mood)
    obs, _  = env.reset()
    ordered, used = [], set()
    for _ in range(len(candidates)):
        action, _ = model.predict(obs, deterministic=True)
        action = int(action)
        if action in used:
            action = next((i for i in range(len(candidates))
                           if i not in used), 0)
        used.add(action)
        ordered.append(candidates[action])
        obs, _, done, _, _ = env.step(action)
        if done:
            break
    return ordered