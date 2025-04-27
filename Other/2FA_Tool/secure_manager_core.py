# secure_totp_manager_core.py

import base64
import sqlite3
import os
import json

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DB_FILE = "secure_totp_secrets.db"
IV_SIZE = 16  # AES IV 大小


def _derive_key(password: str) -> bytes:
    """从用户密码派生对称加密密钥"""
    salt = b"secure_totp_salt"
    kdf = PBKDF2HMAC(
        algorithm=SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return kdf.derive(password.encode())


def _generate_iv() -> bytes:
    """生成随机 IV"""
    return os.urandom(IV_SIZE)


def export_specific_secrets(
    secrets_list: list[tuple[str, str]],
    export_file: str,
    export_password: str,
) -> None:
    """
    导出指定的部分密钥到加密文件。
    :param secrets_list: List[Tuple[name, secret]]
    :param export_file: 目标加密文件路径
    :param export_password: 加密密码
    """
    data_dict: dict[str, str] = {}
    for name, secret in secrets_list:
        if secret and secret != "解密失败":
            data_dict[name] = secret

    data = json.dumps(data_dict)
    key = _derive_key(export_password)
    iv = _generate_iv()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()

    padded = padder.update(data.encode()) + padder.finalize()
    encrypted = encryptor.update(padded) + encryptor.finalize()

    with open(export_file, "wb") as f:
        f.write(iv + encrypted)


class SecureTOTPManager:
    def __init__(self, password: str):
        self.db_file = DB_FILE
        self.conn = self._init_db()
        self.key = None
        self._validate_or_set_password(password)

    def _init_db(self) -> sqlite3.Connection:
        """
        初始化数据库，创建表并做 schema 迁移（添加 algo, counter 列）
        """
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        # 新表定义，包含 algo 和 counter
        create_sql = """
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            secret TEXT NOT NULL,
            iv TEXT NOT NULL,
            algo TEXT NOT NULL DEFAULT 'TOTP',
            counter INTEGER NOT NULL DEFAULT 0
        );
        """
        cur.execute(create_sql)
        # 迁移：如果旧表缺少列，执行 ALTER
        cur.execute("PRAGMA table_info(secrets);")
        cols = [row[1] for row in cur.fetchall()]
        if "algo" not in cols:
            cur.execute(
                "ALTER TABLE secrets ADD COLUMN algo TEXT NOT NULL DEFAULT 'TOTP';"
            )
        if "counter" not in cols:
            cur.execute(
                "ALTER TABLE secrets ADD COLUMN counter INTEGER NOT NULL DEFAULT 0;"
            )
        # 元数据表
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                id INTEGER PRIMARY KEY,
                password_hash TEXT NOT NULL
            );
            """
        )
        conn.commit()
        return conn

    def _validate_or_set_password(self, password: str) -> None:
        """首次设置或验证主密码"""
        cur = self.conn.cursor()
        cur.execute("SELECT password_hash FROM meta WHERE id = 1;")
        row = cur.fetchone()
        derived = _derive_key(password)
        if row is None:
            # 初次设置
            cur.execute(
                "INSERT INTO meta (id, password_hash) VALUES (1, ?);",
                (base64.b64encode(derived).decode(),),
            )
            self.conn.commit()
            self.key = derived
        else:
            stored = base64.b64decode(row[0])
            if stored != derived:
                raise ValueError("密码错误")
            self.key = derived

    def encrypt(self, plaintext: str) -> str:
        """对称加密并返回 Base64 字符串"""
        iv = _generate_iv()
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded = padder.update(plaintext.encode()) + padder.finalize()
        encrypted = encryptor.update(padded) + encryptor.finalize()
        return base64.b64encode(iv + encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        """解密 Base64 格式的密文"""
        data = base64.b64decode(ciphertext.encode())
        iv = data[:IV_SIZE]
        encrypted = data[IV_SIZE:]
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        padded = decryptor.update(encrypted) + decryptor.finalize()
        return (unpadder.update(padded) + unpadder.finalize()).decode()

    def add_secret(
        self,
        name: str,
        secret: str,
        algo: str = "TOTP",
        counter: int = 0,
    ) -> None:
        """
        添加新密钥
        :param name: 唯一名称
        :param secret: Base32 密钥
        :param algo: 'TOTP' or 'HOTP'
        :param counter: 初始计数，仅 HOTP 有效
        """
        encrypted = self.encrypt(secret)
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO secrets (name, secret, iv, algo, counter) "
                "VALUES (?, ?, ?, ?, ?);",
                (name, encrypted, encrypted[:IV_SIZE], algo, counter),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("密钥名称已存在")

    def remove_secret(self, name: str) -> None:
        """删除指定名称的密钥"""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM secrets WHERE name = ?;", (name,))
        self.conn.commit()

    def get_secrets(self) -> list[tuple[str, str, str, int]]:
        """
        获取所有密钥及元数据
        :return: List of (name, secret, algo, counter)
        """
        cur = self.conn.cursor()
        cur.execute("SELECT name, secret, algo, counter FROM secrets;")
        rows = cur.fetchall()
        result: list[tuple[str, str, str, int]] = []
        for name, enc, algo, cnt in rows:
            try:
                sec = self.decrypt(enc)
            except Exception:
                sec = "解密失败"
            result.append((name, sec, algo, cnt))
        return result

    def get_secret_detail(self, name: str) -> tuple[str, str, str, int]:
        """
        获取单条密钥详情
        :return: (name, secret, algo, counter)
        """
        cur = self.conn.cursor()
        cur.execute(
            "SELECT name, secret, algo, counter FROM secrets WHERE name = ?;",
            (name,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("密钥不存在")
        dec = self.decrypt(row[1])
        return (row[0], dec, row[2], row[3])

    def increment_counter(self, name: str) -> None:
        """HOTP 模式下，计数器 +1 并保存"""
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE secrets SET counter = counter + 1 WHERE name = ?;",
            (name,),
        )
        self.conn.commit()

    def export_secrets(self, export_file: str, export_password: str) -> None:
        """
        导出所有密钥（含算法、计数）到加密文件
        """
        all_secrets = self.get_secrets()
        data = {
            name: {"secret": sec, "algo": algo, "counter": cnt}
            for name, sec, algo, cnt in all_secrets
            if sec != "解密失败"
        }
        raw = json.dumps(data)
        key = _derive_key(export_password)
        iv = _generate_iv()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()

        padded = padder.update(raw.encode()) + padder.finalize()
        encrypted = encryptor.update(padded) + encryptor.finalize()

        with open(export_file, "wb") as f:
            f.write(iv + encrypted)

    def import_secrets(self, import_file: str, import_password: str) -> None:
        """
        从加密文件导入密钥（含算法、计数）
        """
        with open(import_file, "rb") as f:
            data = f.read()
        iv = data[:IV_SIZE]
        encrypted = data[IV_SIZE:]
        key = _derive_key(import_password)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

        padded = decryptor.update(encrypted) + decryptor.finalize()
        raw = unpadder.update(padded) + unpadder.finalize()
        loaded = json.loads(raw.decode())

        for name, info in loaded.items():
            sec = info.get("secret")
            algo = info.get("algo", "TOTP")
            cnt = info.get("counter", 0)
            try:
                self.add_secret(name, sec, algo, cnt)
            except ValueError:
                # 已存在则跳过
                continue
