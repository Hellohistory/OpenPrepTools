import hashlib
import random

import requests
import urllib.parse
from config_loader import load_config

config = load_config()


def make_md5(s, encoding='utf-8'):
    return hashlib.md5(s.encode(encoding)).hexdigest()


def translate_baidu_official(query, from_lang='auto', to_lang='en'):
    appid = config['baidu']['appid']
    secret_key = config['baidu']['secret_key']
    salt = str(random.randint(32768, 65536))
    sign = make_md5(appid + query + salt + secret_key)
    query_encoded = urllib.parse.quote(query)
    url = f"https://fanyi-api.baidu.com/api/trans/vip/translate?q={query_encoded}&from={from_lang}&to={to_lang}&appid={appid}&salt={salt}&sign={sign}"
    response = requests.get(url)
    result = response.json()

    if "trans_result" in result:
        return result['trans_result'][0]['dst']
    else:
        raise Exception(result.get("error_msg", "翻译失败"))
