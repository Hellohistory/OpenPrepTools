# totp_core.py

import base64
import hashlib
import hmac
import struct
import time
from typing import Union


class TOTP:
    @staticmethod
    def get_totp_token(secret: str, interval: int = 30) -> str:
        """
        获取 TOTP 验证码
        :param secret: Base32 编码的密钥
        :param interval: 时间间隔（默认30秒）
        :return: 6 位验证码
        :raises ValueError: 密钥无效时抛出
        """
        # 解码 Base32 密钥
        try:
            key = base64.b32decode(secret.upper())
        except Exception:
            raise ValueError("无效的 Base32 密钥")

        # 计算当前时间步
        timestep = int(time.time() // interval)
        timestep_bytes = struct.pack(">Q", timestep)

        # 生成 HMAC-SHA1
        hmac_hash = hmac.new(key, timestep_bytes, hashlib.sha1).digest()

        # 动态截断
        offset = hmac_hash[-1] & 0x0F
        truncated_hash = hmac_hash[offset:offset + 4]
        code_int = struct.unpack(">I", truncated_hash)[0] & 0x7FFFFFFF

        # 返回 6 位验证码，左侧补零
        return f"{code_int % 1_000_000:06}"

    @staticmethod
    def validate_secret(secret: str) -> bool:
        """
        验证 Base32 密钥是否合法
        :param secret: Base32 编码的密钥
        :return: True 或抛出 ValueError
        """
        try:
            base64.b32decode(secret.upper())
            return True
        except Exception:
            raise ValueError("无效的 Base32 密钥")


class HOTP:
    @staticmethod
    def generate_hotp(secret: str, counter: Union[int, str]) -> str:
        """
        生成 HOTP 验证码
        :param secret: Base32 编码的密钥
        :param counter: 计数器值（整数或数字字符串）
        :return: 6 位验证码，左侧补零
        :raises ValueError: 密钥或计数器无效时抛出
        """
        # 解码 Base32 密钥
        try:
            key = base64.b32decode(secret.upper())
        except Exception:
            raise ValueError("无效的 Base32 密钥")

        # 验证并转换计数器为整数
        try:
            counter_int = int(counter)
        except (TypeError, ValueError):
            raise ValueError("计数器必须是整数或数字字符串")

        # 打包计数器（8 字节大端）
        counter_bytes = struct.pack(">Q", counter_int)

        # 生成 HMAC-SHA1
        hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()

        # 动态截断
        offset = hmac_hash[-1] & 0x0F
        truncated_hash = hmac_hash[offset:offset + 4]
        code_int = struct.unpack(">I", truncated_hash)[0] & 0x7FFFFFFF

        # 返回 6 位验证码
        return f"{code_int % 1_000_000:06}"

    @staticmethod
    def validate_secret(secret: str) -> bool:
        """
        验证 Base32 密钥是否合法
        :param secret: Base32 编码的密钥
        :return: True 或抛出 ValueError
        """
        try:
            base64.b32decode(secret.upper())
            return True
        except Exception:
            raise ValueError("无效的 Base32 密钥")
