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


def _derive_key(password):
    """从用户密码派生对称加密密钥"""
    salt = b'secure_totp_salt'
    kdf = PBKDF2HMAC(
        algorithm=SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return kdf.derive(password.encode())


def _generate_iv():
    """生成随机 IV"""
    return os.urandom(IV_SIZE)


def export_specific_secrets(secrets_list, export_file, export_password):
    """
    导出指定的部分密钥到加密文件。
    :param secrets_list: List[Tuple[str, str]]
        外部传入的 (name, secret) 列表，可只导出其中部分。
    :param export_file: str
        目标加密文件路径。
    :param export_password: str
        用于加密导出文件的密码。
    """
    # 只加密 secrets_list 中的数据
    # 形式与 export_secrets 保持一致
    data_dict = {}
    for name, secret in secrets_list:
        # 如果 secret == "解密失败" 可以考虑跳过或抛异常，这里选择跳过
        if secret and secret != "解密失败":
            data_dict[name] = secret

    data_to_encrypt = json.dumps(data_dict)
    derived_key = _derive_key(export_password)
    iv = _generate_iv()
    cipher = Cipher(algorithms.AES(derived_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()

    padded_data = padder.update(data_to_encrypt.encode()) + padder.finalize()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # 写入文件
    with open(export_file, "wb") as file:
        file.write(iv + encrypted_data)


class SecureTOTPManager:
    def __init__(self, password):
        self.db_file = DB_FILE
        self.conn = self._init_db()
        self.key = None
        self._validate_or_set_password(password)

    def _init_db(self):
        """初始化数据库"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            secret TEXT NOT NULL,
            iv TEXT NOT NULL
        );
        """
        create_meta_sql = """
        CREATE TABLE IF NOT EXISTS meta (
            id INTEGER PRIMARY KEY,
            password_hash TEXT NOT NULL
        );
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        cursor.execute(create_meta_sql)
        conn.commit()
        return conn

    def _validate_or_set_password(self, password):
        """验证或设置密码"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT password_hash FROM meta WHERE id = 1")
        result = cursor.fetchone()

        derived_key = _derive_key(password)
        if result is None:
            # 初次设置密码
            cursor.execute(
                "INSERT INTO meta (id, password_hash) VALUES (1, ?)",
                (base64.b64encode(derived_key).decode(),)
            )
            self.conn.commit()
            self.key = derived_key
        else:
            # 验证密码
            stored_hash = base64.b64decode(result[0])
            if stored_hash != derived_key:
                raise ValueError("密码错误")
            self.key = derived_key

    def encrypt(self, plaintext):
        """加密数据"""
        iv = _generate_iv()
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(plaintext.encode()) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(iv + encrypted_data).decode()

    def decrypt(self, ciphertext):
        """解密数据"""
        data = base64.b64decode(ciphertext.encode())
        iv = data[:IV_SIZE]
        encrypted_data = data[IV_SIZE:]
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
        return (unpadder.update(decrypted_padded) + unpadder.finalize()).decode()

    def add_secret(self, name, secret):
        """添加密钥"""
        encrypted_secret = self.encrypt(secret)
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO secrets (name, secret, iv) VALUES (?, ?, ?)",
                (name, encrypted_secret, encrypted_secret[:IV_SIZE]),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("密钥名称已存在")

    def remove_secret(self, name):
        """删除密钥"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM secrets WHERE name = ?", (name,))
        self.conn.commit()

    def get_secrets(self):
        """获取所有密钥并解密"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, secret FROM secrets")
        rows = cursor.fetchall()
        secrets = []
        for name, encrypted_secret in rows:
            try:
                decrypted_secret = self.decrypt(encrypted_secret)
                secrets.append((name, decrypted_secret))
            except Exception:
                secrets.append((name, "解密失败"))
        return secrets

    def export_secrets(self, export_file, export_password):
        """导出所有密钥到加密文件"""
        secrets = self.get_secrets()
        data_to_encrypt = json.dumps({name: secret for name, secret in secrets if secret != "解密失败"})
        derived_key = _derive_key(export_password)
        iv = _generate_iv()
        cipher = Cipher(algorithms.AES(derived_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(data_to_encrypt.encode()) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        with open(export_file, "wb") as file:
            file.write(iv + encrypted_data)

    def import_secrets(self, import_file, import_password):
        """从加密文件导入密钥"""
        with open(import_file, "rb") as file:
            data = file.read()
        iv = data[:IV_SIZE]
        encrypted_data = data[IV_SIZE:]
        derived_key = _derive_key(import_password)
        cipher = Cipher(algorithms.AES(derived_key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
        decrypted_data = unpadder.update(decrypted_padded) + unpadder.finalize()
        secrets = json.loads(decrypted_data.decode())
        for name, secret in secrets.items():
            try:
                self.add_secret(name, secret)
            except ValueError:
                print(f"密钥 {name} 已存在，跳过导入。")
