## 1.前言

离线2FA验证器当中核心的算法实现是基于 `totp_hotp_core.py` 代码实现，其中一个用于生成和验证 TOTP（Time-based One-Time Password，基于时间的一次性密码）的类。TOTP 是一种动态口令认证方式，常见于双重认证（2FA）中。
## 2. 技术简介

TOTP（Time-based One-Time Password）是一种广泛应用于身份验证的安全机制，常见于 Google Authenticator、Microsoft Authenticator 等认证工具中。
TOTP 的核心原理是基于当前的时间戳和一个共享的密钥（通常是 Base32 编码的密钥）生成一个短期有效的动态验证码，通常是 6 位数字。该验证码会在每个时间周期（如每 30 秒）更新一次。

本文将详细讲解 `totp_hotp_core.py` 代码实现，分析 TOTP 验证码的生成和密钥验证过程。

## 3. TOTP 算法原理讲解

TOTP 基于哈希和时间的结合，确保每个时间步长内生成的验证码是唯一且时效性的。其安全性依赖于密钥的保密性和算法的设计。每次生成验证码时，使用当前的时间步长和密钥进行哈希计算，这样即使是同一个密钥，每个时间段生成的验证码也会不同。

## 4. 代码结构介绍

`totp_hotp_core.py` 中的 `TOTP` 类包含两个静态方法：`get_totp_token` 和 `validate_secret`。这两个方法分别用于生成 TOTP 验证码和验证 Base32 编码的密钥。

### 4.1 `get_totp_token` 方法

`get_totp_token` 方法用于生成基于时间的一次性密码。其核心流程如下：

```python
def get_totp_token(secret: str, interval: int = 30) -> str:
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
```

#### 4.1.1 解码 Base32 密钥

第一步是对传入的 `secret`（Base32 编码的密钥）进行解码。这里的密钥在实际应用中通常由服务器生成，并且与客户端共享，这里的使用场景，例如像是Github或者X等平台需要用户设置2FA验证的时候，会给你一个Base32编码的秘钥。`base64.b32decode` 函数用于将密钥从 Base32 编码转换为二进制数据。

```python
key = base64.b32decode(secret.upper())
```

如果密钥格式不正确，程序会抛出异常并提示用户 "无效的 Base32 密钥"。

#### 4.1.2 计算时间步长

TOTP 算法基于当前时间生成验证码，因此接下来需要计算当前时间的时间步长（`timestep`）。时间步长通常为 30 秒。通过 `time.time()` 获取当前的 Unix 时间戳（这里是以秒为单位），然后将其除以时间间隔 `interval`（默认 30 秒），得到一个整数值。

```python
timestep = int(time.time() // interval)
```

#### 4.1.3 使用 HMAC-SHA1 生成哈希

接下来，使用 HMAC（基于哈希的消息认证码）算法结合 SHA-1 哈希函数来生成一个固定长度的哈希值。HMAC 需要两个参数：密钥和消息。这里的消息就是我们上面计算出的时间步长，经过 `struct.pack(">Q", timestep)` 打包成 8 字节的大端格式数据。

```python
timestep_bytes = struct.pack(">Q", timestep)
hmac_hash = hmac.new(key, timestep_bytes, hashlib.sha1).digest()
```

#### 4.1.4 提取 OTP

从 HMAC 哈希值中提取最终的 OTP（一次性密码）。首先，取哈希结果的最后一个字节的低 4 位，作为偏移量（`offset`）。然后，使用这个偏移量从哈希值中提取 4 字节的子串，并将其解包为一个整数。接着，通过与 `0x7FFFFFFF` 相与，确保结果为正数。

```python
offset = hmac_hash[-1] & 0x0F
truncated_hash = hmac_hash[offset:offset + 4]
code = struct.unpack(">I", truncated_hash)[0] & 0x7FFFFFFF
```

最后，生成 6 位的验证码，即 `code % 1000000`，并返回作为字符串。

```python
return f"{code % 1000000:06}"
```

#### 4.1.5 返回验证码

返回的是一个 6 位数的字符串，表示当前时间步长内的验证码。每个时间段（通常为 30 秒），该验证码都会变化，确保其时效性。

### 4.2 `validate_secret` 方法

`validate_secret` 方法用于验证传入的密钥是否合法，即是否是有效的 Base32 编码格式。

```python
def validate_secret(secret: str) -> bool:
    try:
        base64.b32decode(secret.upper())
        return True
    except Exception:
        raise ValueError("无效的 Base32 密钥")
```

该方法通过 `base64.b32decode` 尝试解码密钥，如果解码成功，说明密钥有效，返回 `True`；如果解码失败，则抛出 `ValueError` 异常，提示 "无效的 Base32 密钥"。


`totp_core.py` 中的 `TOTP` 类实现了基于时间的一次性密码生成与验证功能。通过 HMAC、SHA-1 和 Base32 编码，结合当前时间的时间步长，生成动态验证码，增强了系统的安全性。

## 5.完整 totp_core.py

```Python
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
        """        try:  
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
        """        try:  
            base64.b32decode(secret.upper())  
            return True  
        except Exception:  
            raise ValueError("无效的 Base32 密钥")
```