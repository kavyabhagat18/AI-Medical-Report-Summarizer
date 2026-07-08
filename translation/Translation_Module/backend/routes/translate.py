from fastapi import APIRouter

from backend.models.request_models import TranslationRequest
from backend.models.response_models import TranslationResponse

from translation.translator import translate

router = APIRouter()

@router.post("/translate", response_model=TranslationResponse)

def translate_report(request: TranslationRequest):

    translated = translate(
        request.text,
        request.language
    )

    return TranslationResponse(
        translated_text=translated
    )