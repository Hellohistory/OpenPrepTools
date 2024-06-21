# password_generation.py

import hashlib
import secrets
import string

from random_number import RandomDataEnhancer


def _create_mixed_hash(hash_value):
    hash_sha256 = hashlib.sha256(hash_value.encode('utf-8')).hexdigest()
    hash_md5 = hashlib.md5(hash_value.encode('utf-8')).hexdigest()
    reversed_hash = (hash_sha256 + hash_md5)[::-1]
    return hashlib.sha256(reversed_hash.encode('utf-8')).hexdigest() + hashlib.md5(
        reversed_hash.encode('utf-8')).hexdigest()


def _concatenate_and_swap(mixed_hash_value):
    concatenate_times = secrets.randbelow(5) + 1  # [1, 5]
    for _ in range(concatenate_times):
        mixed_hash_value += hashlib.sha256(mixed_hash_value.encode('utf-8')).hexdigest()

    mixed_hash_list = list(mixed_hash_value)
    swap_times = secrets.randbelow(10) + 1  # [1, 10]
    for _ in range(swap_times):
        idx1, idx2 = secrets.SystemRandom().sample(range(len(mixed_hash_list)), 2)
        mixed_hash_list[idx1], mixed_hash_list[idx2] = mixed_hash_list[idx2], mixed_hash_list[idx1]

    return ''.join(mixed_hash_list)


class PasswordGenerator:
    CHAR_SET_MAP = {
        'lowercase': (string.ascii_lowercase, 1),  # 小写字母
        'uppercase': (string.ascii_uppercase, 1),  # 大写字母
        'digits': (string.digits, 1),  # 数字
        'punctuation': (string.punctuation, 1)  # 标点符号
    }

    def __init__(self, base_length=10, char_types=None):
        if char_types is None:
            char_types = ['lowercase', 'uppercase', 'digits', 'punctuation']
        self.base_length = base_length
        self.char_sets = self._initialize_char_sets(char_types)

    def _initialize_char_sets(self, char_types):
        """
        初始化字符集。
        :param char_types: 一个包含字符类型的列表，例如 ['lowercase', 'digits']
        :return: 根据指定类型组合的字符集列表
        """
        return [self.CHAR_SET_MAP[char_type] for char_type in char_types if char_type in self.CHAR_SET_MAP]

    def generate_password(self, hash_value):
        mixed_hash_value = _create_mixed_hash(hash_value)
        _concatenate_and_swap(mixed_hash_value)
        return self._create_password()

    def _create_password(self):
        # 确保密码长度严格按照用户指定的 base_length
        password_length = self.base_length
        password_chars = []

        # 根据密码类型，从对应的字符集中选择字符
        for i in range(password_length):
            weights = [weight for _, weight in self.char_sets]
            char_set, _ = secrets.SystemRandom().choices(self.char_sets, weights=weights, k=1)[0]
            password_chars.append(secrets.choice(char_set))
        return ''.join(password_chars)

    def password_generator(self):
        enhancer = RandomDataEnhancer()
        random_hash = enhancer.main()
        password = self.generate_password(random_hash)
        return password
