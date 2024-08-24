from fastapi import HTTPException, APIRouter
from pydantic import BaseModel, Field

from naming_utils import format_variable_name, NAMING_STYLES
from translation_source.translation_utils import translate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class NamingRequest(BaseModel):
    content: str = Field(..., title="输入内容", description="需要翻译和格式化的原始内容，例如变量名或文本。")
    naming_type: str = Field(None, title="命名类型",
                             description="可为空，变量的命名风格，例如 snake_case、camelCase、PascalCase 等。")
    from_lang: str = Field(..., title="源语言", description="原始内容的语言，例如 'zh' 表示中文。")
    to_lang: str = Field(..., title="目标语言", description="翻译后的目标语言，例如 'en' 表示英文。")


@router.post("/generate_name", operation_id="generate_name")
def generate_name(request: NamingRequest):
    try:
        translated_name = translate(request.content, from_lang=request.from_lang, to_lang=request.to_lang)
        logger.info(f"Translated name: {translated_name}")
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    # 只有中文转英文时支持格式化处理
    if request.from_lang == 'zh' and request.to_lang == 'en':
        if request.naming_type:
            if request.naming_type not in NAMING_STYLES:
                raise HTTPException(status_code=400, detail="不支持的命名类型")

            formatted_name = format_variable_name(translated_name, style=request.naming_type)
            return {"translated_name": translated_name, "formatted_name": formatted_name}

        else:
            formatted_names = {}
            for style in NAMING_STYLES:
                formatted_names[style] = format_variable_name(translated_name, style=style)

            return {"translated_name": translated_name, "formatted_names": formatted_names}

    # 对于其他语言组合，直接返回翻译后的内容
    return {"translated_name": translated_name}
