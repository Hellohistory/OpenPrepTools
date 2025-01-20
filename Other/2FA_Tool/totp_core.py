# totp_core.py

import base64
import hashlib
import hmac
import struct
import time


class TOTP:
    @staticmethod
    def get_totp_token(secret: str, interval: int = 30) -> str:
        """
        获取 TOTP 验证码
        :param secret: Base32 编码的密钥
        :param interval: 时间间隔（默认30秒）
        :return: 6 位验证码
        """
        try:
            key = base64.b32decode(secret.upper())
        except Exception:
            raise ValueError("无效的 Base32 密钥")

        timestep = int(time.time() // interval)
        timestep_bytes = struct.pack(">Q", timestep)
        hmac_hash = hmac.new(key, timestep_bytes, hashlib.sha1).digest()
        offset = hmac_hash[-1] & 0x0F
        truncated_hash = hmac_hash[offset:offset + 4]
        code = struct.unpack(">I", truncated_hash)[0] & 0x7FFFFFFF
        return f"{code % 1000000:06}"

    @staticmethod
    def validate_secret(secret: str) -> bool:
        """
        验证密钥是否合法
        :param secret: Base32 编码的密钥
        :return: True 或抛出异常
        """
        try:
            base64.b32decode(secret.upper())
            return True
        except Exception:
            raise ValueError("无效的 Base32 密钥")
