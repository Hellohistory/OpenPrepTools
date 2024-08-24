import hashlib
import requests
import time
import random


def md5Encrypt(obj):
    md5 = hashlib.md5()
    md5.update(obj.encode())
    return md5.hexdigest()


def youdao_translate_free(search_key: str, to: str, lang: str = 'AUTO') -> str:
    ts = int(time.time() * 1000)
    salt = str(ts) + str(random.randint(1, 9))
    bv = md5Encrypt(
        '5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36')
    sign = md5Encrypt("fanyideskweb" + search_key + salt + "Tbh5E8=q6U3EXe+&L[4c@")

    url = 'http://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
    headers = {

        'Host': 'fanyi.youdao.com',
        'Origin': 'http://fanyi.youdao.com',
        'Referer': 'http://fanyi.youdao.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/88.0.4324.190 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': 'OUTFOX_SEARCH_USER_ID=-1644523005@10.108.160.100; OUTFOX_SEARCH_USER_ID_NCOO=857549368.4207594; '
                  'JSESSIONID=aaahQdbLzSjY3dSU_V1Fx; DICT_UGC=be3af0da19b5c5e6aa4e17bd8d90b28a|; '
                  'JSESSIONID=abcXf1BO34WgqbzPvg3Fx; _ntes_nnid=550e7be268d446cac20d6f763fbdc8c7,1614758394523; '
                  '___rl__test__cookies=1615258741826'
    }
    data = {
        "i": search_key,
        "lang": lang,
        "to": to,
        "smartresult": "dict",
        "client": "fanyideskweb",
        "salt": salt,
        "sign": sign,
        "lts": ts,
        "bv": bv,
        "doctype": "json",
        "version": "2.1",
        "keyfrom": "fanyi.web",
        "action": "FY_BY_REALTlME"
    }

    try:
        res = requests.post(url, headers=headers, data=data).json()
        return res['translateResult'][0][0]['tgt']
    except Exception as e:
        raise Exception(f"翻译失败: {e}")