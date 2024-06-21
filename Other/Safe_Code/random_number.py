# random_number.py

import hashlib
import os
import secrets
import time
import concurrent.futures


class RandomDataEnhancer:
    def __init__(self):
        self.system_random = secrets.SystemRandom()
        self.logistic_r = self.system_random.uniform(3.57, 4.0)  # Logistic映射的参数选择在混沌区间

    def logistic_map(self, x):
        """Logistic映射，用于生成混沌序列。"""
        return self.logistic_r * x * (1 - x)

    def generate_chaotic_sequence(self, count=100):
        """生成一个混沌序列作为随机数源。使用系统随机数生成器确定初始值。"""
        x = self.system_random.random()  # 使用系统随机数生成器确定初始值
        return [self.logistic_map(x := self.logistic_map(x)) for _ in range(count)]

    def generate_random_floats(self, count=7000, start=1, end=10000000):
        """
        生成指定数量的随机浮点数列表。
        """
        return [self.system_random.uniform(start, end) for _ in range(count)]

    def generate_random_ints(self, count=8000, start=10000, end=6000000000):
        """
        生成指定数量的随机整数列表。
        """
        return [self.system_random.randint(start, end) for _ in range(count)]

    def shuffle_and_select(self, nums, sample_size=15000):
        """
        将数字列表随机打乱，并选择指定数量的样本。
        """
        self.system_random.shuffle(nums)
        return self.system_random.sample(nums, min(len(nums), sample_size))

    def append_system_info(self, nums):
        """
        添加系统时间和操作系统类型到数字列表中。
        """
        return nums + [time.time(), hash(os.name), os.getpid(), self.system_random.randrange(1000000)]

    def enhance_randomness(self, data_str, enable_extra=True):
        """
        对数据字符串进行复杂的随机性增强，此处添加混沌序列。
        """
        if not enable_extra:
            return data_str

        # 添加混沌序列
        chaotic_sequence = ''.join(map(str, self.generate_chaotic_sequence()))
        data_str += chaotic_sequence

        # 剩余增强操作
        operations = ['reverse', 'shuffle', 'insert', 'delete']
        for _ in range(secrets.randbelow(10) + 1):  # [1, 10]
            operation = self.system_random.choice(operations)
            if operation == 'reverse':
                data_str = data_str[::-1]
            elif operation == 'shuffle':
                data_str = ''.join(self.system_random.sample(data_str, len(data_str)))
            elif operation == 'insert':
                insert_pos = self.system_random.randint(0, len(data_str))
                data_str = data_str[:insert_pos] + secrets.token_hex(1) + data_str[insert_pos:]
            elif operation == 'delete' and len(data_str) > 1:
                delete_pos = self.system_random.randint(0, len(data_str) - 1)
                data_str = data_str[:delete_pos] + data_str[delete_pos + 1:]

        return data_str

    def generate_final_hash(self, data):
        """
        生成最终的哈希值。
        """
        hash_func = self.system_random.choice([hashlib.sha256, hashlib.sha512, hashlib.sha3_256, hashlib.sha3_512])
        return hash_func(data.encode()).hexdigest()

    def main(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            floats_future = executor.submit(self.generate_random_floats)
            ints_future = executor.submit(self.generate_random_ints)

            floats = floats_future.result()
            ints = ints_future.result()

        all_nums = floats + ints

        selected_nums = self.shuffle_and_select(all_nums)
        selected_with_info = self.append_system_info(selected_nums)
        num_str = convert_to_string(selected_with_info)

        hashes = generate_hashes(num_str)
        concatenated_hashes = ''.join(hashes)

        salted_hashed = salt_and_hash(concatenated_hashes)
        final_hash_with_randomness = self.enhance_randomness(salted_hashed, enable_extra=True)

        final_hash = self.generate_final_hash(final_hash_with_randomness)

        return final_hash


def incorporate_process_info(data_str):
    """融合程序进程信息到数据字符串。"""
    process_info = f"{time.time()}{os.getpid()}{os.getloadavg()[0]}"
    return data_str + process_info


def generate_hashes(data_str):
    """
    生成多种哈希值。
    """
    hash_types = [hashlib.md5, hashlib.sha1, hashlib.sha256, hashlib.blake2b, hashlib.blake2s, hashlib.sha3_256,
                  hashlib.sha3_512]
    return [hash_func(data_str.encode()).hexdigest() for hash_func in hash_types]


def convert_to_string(nums):
    """
    将数字列表转换为字符串。
    """
    return ''.join(map(str, nums))


def salt_and_hash(concatenated_hashes):
    """
    对哈希结果添加随机盐，并进行进一步的哈希计算。
    """
    salt = secrets.token_bytes(16).hex()
    salted_data = concatenated_hashes + salt
    final_hash_types = [hashlib.sha256, hashlib.sha512, hashlib.sha3_256, hashlib.sha3_512]
    return ''.join([hash_func(salted_data.encode()).hexdigest() for hash_func in final_hash_types])
