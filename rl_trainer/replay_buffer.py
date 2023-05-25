import numpy as np
import torch
import copy
import hashlib


class ReplayBuffer:
    def __init__(self, args):
        self.N = args.N
        self.obs_dim = args.obs_dim
        self.state_dim = args.state_dim
        self.action_dim = args.action_dim
        self.episode_limit = args.episode_length
        self.buffer_size = args.buffer_size
        self.batch_size = args.batch_size
        self.episode_num = 0
        self.current_size = 0
        self.buffer = {'obs_n': np.zeros([self.buffer_size, self.episode_limit + 1, self.N, self.obs_dim]),
                       's': np.zeros([self.buffer_size, self.episode_limit + 1, self.state_dim]),
                       'avail_a_n': np.ones([self.buffer_size, self.episode_limit + 1, self.N, self.action_dim]),  # Note: We use 'np.ones' to initialize 'avail_a_n'
                       'last_onehot_a_n': np.zeros([self.buffer_size, self.episode_limit + 1, self.N, self.action_dim]),
                       'a_n': np.zeros([self.buffer_size, self.episode_limit, self.N]),
                       'r': np.zeros([self.buffer_size, self.episode_limit, 1]),
                       'dw': np.ones([self.buffer_size, self.episode_limit, 1]),  # Note: We use 'np.ones' to initialize 'dw'
                       'active': np.zeros([self.buffer_size, self.episode_limit, 1])
                       }
        self.episode_len = np.zeros(self.buffer_size)

    def hash_dict(self,dictonary):
        hash_func=hashlib.md5();
        string=str(dictonary);
        hash_func.update(string.encode());
        val=hash_func.digest();
        #print('value:',val);
        val=int.from_bytes(val);
        
        val=int(val%(1e9+3));
        #print('value:',val);
        return val;

    def store_transition(self, episode_step, obs_n, s, avail_a_n, last_onehot_a_n, a_n, r, dw):
        self.buffer['obs_n'][self.episode_num][episode_step] = obs_n
        self.buffer['s'][self.episode_num][episode_step] = self.hash_dict(s)
        self.buffer['avail_a_n'][self.episode_num][episode_step] = avail_a_n
        self.buffer['last_onehot_a_n'][self.episode_num][episode_step + 1] = last_onehot_a_n
        self.buffer['a_n'][self.episode_num][episode_step] = a_n
        self.buffer['r'][self.episode_num][episode_step] = np.sum(r[0:3]);
        self.buffer['dw'][self.episode_num][episode_step] = dw

        self.buffer['active'][self.episode_num][episode_step] = 1.0

    def store_last_step(self, episode_step, obs_n, s, avail_a_n):
        self.buffer['obs_n'][self.episode_num][episode_step] = obs_n
        self.buffer['s'][self.episode_num][episode_step] = self.hash_dict(s)
        self.buffer['avail_a_n'][self.episode_num][episode_step] = avail_a_n
        self.episode_len[self.episode_num] = episode_step  # Record the length of this episode
        self.episode_num = (self.episode_num + 1) % self.buffer_size
        self.current_size = min(self.current_size + 1, self.buffer_size)

    def sample(self):
        # Randomly sampling
        index = np.random.choice(self.current_size, size=self.batch_size, replace=False)
        max_episode_len = int(np.max(self.episode_len[index]))
        batch = {}
        for key in self.buffer.keys():
            if key == 'obs_n' or key == 's' or key == 'avail_a_n' or key == 'last_onehot_a_n':
                batch[key] = torch.tensor(self.buffer[key][index, :max_episode_len + 1], dtype=torch.float32)
            elif key == 'a_n':
                batch[key] = torch.tensor(self.buffer[key][index, :max_episode_len], dtype=torch.long)
            else:
                batch[key] = torch.tensor(self.buffer[key][index, :max_episode_len], dtype=torch.float32)

        return batch, max_episode_len
