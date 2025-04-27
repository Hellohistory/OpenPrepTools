# HOTP 算法详解

## 1. 前言

HOTP（HMAC-based One-Time Password，基于 HMAC 的一次性密码）是一种广泛应用于身份验证的安全机制，是许多双因素认证系统的基础。与 TOTP（基于时间）不同，HOTP 是基于计数器的一次性密码算法。

本文将详细解析 `HOTP` 类的实现，包括 HOTP 验证码的生成和密钥验证过程。

## 2. 技术简介

HOTP 是 RFC 4226 定义的标准算法，其核心原理是基于一个共享密钥和递增的计数器值，通过 HMAC 算法生成一次性密码。HOTP 密码通常为 6 位数字，每次认证后计数器递增，确保每次生成的密码都不同。

## 3. HOTP 算法原理讲解

HOTP 算法通过以下公式定义：
```
HOTP(K, C) = Truncate(HMAC-SHA-1(K, C)) 
```
其中：
- K 是共享密钥
- C 是计数器值
- Truncate 是动态截断函数，将 HMAC 结果转换为数字

HOTP 的安全性依赖于：
1. 密钥的保密性
2. HMAC 算法的单向性
3. 计数器的严格递增

## 4. 代码结构介绍

`HOTP` 类包含两个静态方法：`generate_hotp` 和 `validate_secret`，分别用于生成 HOTP 验证码和验证 Base32 编码的密钥。

### 4.1 `generate_hotp` 方法

`generate_hotp` 方法用于生成基于计数器的一次性密码。其核心流程如下：

```python
@staticmethod
def generate_hotp(secret: str, counter: Union[int, str]) -> str:
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
```

#### 4.1.1 解码 Base32 密钥

第一步是对传入的 `secret`（Base32 编码的密钥）进行解码。`base64.b32decode` 函数用于将密钥从 Base32 编码转换为二进制数据。

```python
try:
    key = base64.b32decode(secret.upper())
except Exception:
    raise ValueError("无效的 Base32 密钥")
```

如果密钥格式不正确，程序会抛出异常并提示用户 "无效的 Base32 密钥"。

#### 4.1.2 处理计数器值

HOTP 使用计数器而非时间戳作为变量。计数器可以是整数或数字字符串：

```python
try:
    counter_int = int(counter)
except (TypeError, ValueError):
    raise ValueError("计数器必须是整数或数字字符串")
```

#### 4.1.3 打包计数器值

计数器值需要转换为 8 字节的大端序字节串：

```python
counter_bytes = struct.pack(">Q", counter_int)
```

`>Q` 表示：
- `>` 表示大端序
- `Q` 表示 8 字节无符号长整型

#### 4.1.4 生成 HMAC-SHA1 哈希

使用 HMAC-SHA1 算法生成哈希值：

```python
hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()
```

#### 4.1.5 动态截断处理

HOTP 使用动态截断（Dynamic Truncation）从 HMAC 结果中提取有效部分：

1. 取最后一个字节的低 4 位作为偏移量：
```python
offset = hmac_hash[-1] & 0x0F
```

2. 从偏移量开始取 4 字节：
```python
truncated_hash = hmac_hash[offset:offset + 4]
```

3. 转换为整数并屏蔽最高位：
```python
code_int = struct.unpack(">I", truncated_hash)[0] & 0x7FFFFFFF
```

#### 4.1.6 生成 6 位验证码

最后将整数模 1,000,000 并格式化为 6 位数字：

```python
return f"{code_int % 1_000_000:06}"
```

### 4.2 `validate_secret` 方法

`validate_secret` 方法与 TOTP 中的实现相同，用于验证 Base32 密钥的有效性：

```python
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
```

## 5. 完整 HOTP 实现代码

```python
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
```
