import random


class Sampler:

    def __init__(self, *, sample_percentage: float = None, sample_n=None, seed=None):
        """
        Can only specify one of these parameters
        :param sample_percentage: The percentage of each list to sample (0 < sample_percentage <= 1)
        :param sample_n: The number of items to sample from each list (sample_n > 0)
        """
        if (sample_percentage is None) == (sample_n is None):
            raise ValueError("Exactly one of sample_percentage or sample_n must be specified")

        if sample_percentage is not None:
            if not (0 < sample_percentage <= 1):
                raise ValueError("sample_percentage must be between 0 and 1")

        if sample_n is not None:
            if sample_n <= 0:
                raise ValueError("sample_n must be greater than 0")

        self.sample_percentage = sample_percentage
        self.sample_n = sample_n
        self.random_gen = random.Random(seed)

    def get_sample(self, items: dict[str, list]) -> dict[str, list]:
        """
        Given a dictionary where the key is list id, and the value is a list,
        return a new dictionary with a sampled list per key based on the sampling configuration.
        """

        sampled_dict = {}

        for key, value_list in items.items():
            if self.sample_percentage is not None:
                n_samples = int(len(value_list) * self.sample_percentage)
            else:
                n_samples = min(self.sample_n, len(value_list))

            sampled_dict[key] = self.random_gen.sample(value_list, n_samples)

        return sampled_dict
