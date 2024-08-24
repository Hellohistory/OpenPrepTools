from translation_source.baidu_official import translate_baidu_official
from translation_source.baidu_free import translate_baidu_free
from translation_source.youdao_free import youdao_translate_free
from config_loader import load_config

config = load_config()


def translate(query, from_lang='auto', to_lang='en'):
    source = config.get('default_translation_source', 'baidu')

    if source == 'baidu_official':
        return translate_baidu_official(query, from_lang=from_lang, to_lang=to_lang)
    elif source == 'baidu_free':
        return translate_baidu_free(query, from_lang=from_lang, to_lang=to_lang)
    elif source == 'youdao_free':
        return youdao_translate_free(query, to=to_lang, lang=from_lang)
    else:
        raise ValueError("不支持的翻译源")
