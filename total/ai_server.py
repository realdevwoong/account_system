from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

class AIPayload(BaseModel):
    message: str
    account_info: str

@app.post("/ai")
def get_ai_response(payload: AIPayload):
    system_prompt = f"""
너는 은행 계좌 정보를 기반으로 금융 상담을 해주는 친절한 한국어 챗봇이야.

아래는 사용자의 계좌 정보야. 모든 정보는 신뢰할 만하며, 질문에 답변할 때 꼭 참고해:
{payload.account_info}

응답을 구성할 때는 다음을 반영해:
- 각 계좌의 상품명, 이자율, 잔액, 만기일, 자동이체 여부 등을 기반으로 정리하거나 조언해줘
- 숫자는 천단위로 쉼표를 찍고, %, 원 등의 단위를 붙여
- 질문이 없더라도 계좌정보의 특징을 요약해서 말해줘
- 필요한 경우 사용자가 어떤 계좌를 어떻게 활용할 수 있을지 상담해줘
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": payload.message}
        ]
    )
    return {"response": response.choices[0].message.content.strip()}