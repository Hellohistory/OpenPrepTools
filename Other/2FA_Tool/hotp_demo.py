import secrets
import base64
import hmac
import hashlib
import struct


def generate_hotp_secret(length: int = 20) -> str:
    """
    生成 HOTP/TOTP 通用的 Base32 密钥
    :param length: 随机字节长度，默认 20
    :return: Base32 编码的密钥（去除 '=' 填充）
    """
    random_bytes = secrets.token_bytes(length)
    # Base32 编码并去掉末尾的 '='
    secret = base64.b32encode(random_bytes).decode('utf-8').rstrip('=')
    return secret


def generate_hotp_code(secret: str, counter: int, digits: int = 6) -> str:
    """
    根据计数器生成 HOTP 验证码
    :param secret: Base32 编码的密钥
    :param counter: HOTP 计数器值（必须与服务器同步）
    :param digits: 验证码位数，默认 6 位
    :return: 固定位数的验证码字符串
    """
    # 解码密钥
    key = base64.b32decode(secret.upper())
    # 将计数器打包为 8 字节大端整数
    counter_bytes = struct.pack(">Q", counter)
    # 计算 HMAC-SHA1
    hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()
    # 动态截断，取最后一个字节低 4 位作为偏移量
    offset = hmac_hash[-1] & 0x0F
    truncated = hmac_hash[offset:offset + 4]
    # 转换为无符号 31 位整数
    code_int = struct.unpack(">I", truncated)[0] & 0x7FFFFFFF
    # 对 10^digits 取模，左侧补零
    return f"{code_int % (10 ** digits):0{digits}d}"


if __name__ == "__main__":
    # 演示：先生成一个 Base32 密钥，然后计算不同计数器下的 HOTP
    secret = generate_hotp_secret(20)
    print(f"生成的 Base32 密钥：{secret}\n")

    # 示例多个计数器值
    for counter in range(1, 6):
        code = generate_hotp_code(secret, counter)
        print(f"HOTP @{counter:>2} -> {code}")
