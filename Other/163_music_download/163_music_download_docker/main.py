from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import json
import httpx
import os
from hashlib import md5
from random import randrange
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import logging
from functools import lru_cache
from logging.handlers import RotatingFileHandler

FILE_DIR = "file"
os.makedirs(FILE_DIR, exist_ok=True)

# 大小超过 1MB 自动归零
log_path = os.path.join(FILE_DIR, 'app.log')
handler = RotatingFileHandler(log_path, maxBytes=1 * 1024 * 1024, backupCount=1)
logging.basicConfig(level=logging.INFO, handlers=[handler],
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()


class Settings:
    cookie_path: str = os.getenv("COOKIE_PATH", os.path.join(FILE_DIR, "cookie.txt"))  # 使用环境变量来动态设置 cookie 文件路径


@lru_cache()
def get_settings():
    return Settings()


async def load_cookie(settings: Settings = Depends(get_settings)):
    if not os.path.exists(settings.cookie_path):
        logger.error("cookie.txt 文件未找到")
        raise HTTPException(status_code=404, detail="cookie.txt 文件未找到，请确保文件存在且包含有效的 Cookie")
    with open(settings.cookie_path, "r") as f:
        cookie_content = f.read().strip()
        if not cookie_content:
            logger.error("cookie.txt 文件为空")
            raise HTTPException(status_code=400, detail="cookie.txt 文件为空，请确保文件包含有效的 Cookie")
        logger.info("Cookie successfully loaded")
        return {"MUSIC_U": cookie_content}


class SongRequest(BaseModel):
    id: int
    level: str  # 'standard', 'exhigh', 'lossless', 'hires', 'jyeffect', 'sky', 'jymaster'


def hash_digest(text):
    return md5(text.encode("utf-8")).digest()


def hex_digest(data):
    return "".join([hex(d)[2:].zfill(2) for d in data])


def hash_hex_digest(text):
    return hex_digest(hash_digest(text))


async def generate_params(song_id, level):
    url = "https://interface3.music.163.com/eapi/song/enhance/player/url/v1"
    aes_key = b"e82ckenh8dichen8"
    config = {
        "os": "pc",
        "appver": "",
        "osver": "",
        "deviceId": "pyncm!",
        "requestId": str(randrange(20000000, 30000000))
    }

    payload = {
        'ids': [song_id],
        'level': level,
        'encodeType': 'flac',
        'header': json.dumps(config),
    }

    if level == 'sky':
        payload['immerseType'] = 'c51'

    url_path = "/api/song/enhance/player/url/v1"
    digest = hash_hex_digest(f"nobody{url_path}use{json.dumps(payload)}md5forencrypt")
    params = f"{url_path}-36cd479b6b5-{json.dumps(payload)}-36cd479b6b5-{digest}"
    padder = padding.PKCS7(algorithms.AES(aes_key).block_size).padder()
    padded_data = padder.update(params.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(aes_key), modes.ECB())
    encryptor = cipher.encryptor()
    enc = encryptor.update(padded_data) + encryptor.finalize()
    return hex_digest(enc)


async def post_request(url, params, cookies):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36 Chrome/91.0.4472.164 NeteaseMusicDesktop/2.10.2.200154',
        'Referer': '',
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, cookies=cookies, data={"params": params}, timeout=10)
        response.raise_for_status()
        return response.json()


@app.post("/song/url")
async def get_song_url(request: SongRequest, cookies: dict = Depends(load_cookie)):
    try:
        params = await generate_params(request.id, request.level)
        result = await post_request("https://interface3.music.163.com/eapi/song/enhance/player/url/v1", params, cookies)
        return result
    except httpx.RequestError as e:
        logger.error(f"An error occurred while requesting {e.request.url!r}")
        raise HTTPException(status_code=500, detail="请求音乐服务时出错")
    except httpx.HTTPStatusError as e:
        logger.error(f"Error response {e.response.status_code} while requesting {e.request.url!r}")
        raise HTTPException(status_code=e.response.status_code, detail="音乐服务返回了错误响应")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=36925)