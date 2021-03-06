import os
from typing import Dict, List

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Security, Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader, APIKey
from pydantic import BaseModel
from starlette.status import HTTP_403_FORBIDDEN

from powerskill import extractor, models

load_dotenv()
app = FastAPI()


class Values(BaseModel):
    values: List = []


class Value(Values):
    recordId: str
    data: Dict[str, str] = None


API_KEY = os.environ['KEY']
API_KEY_NAME = "Ocp-Apim-Subscription-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
summarizer_model = models.Models(summarizer_model=None)


@app.on_event("startup")
async def startup_event():
    summarizer_model.load_summarisation_model(os.environ['SUMMARIZER_MODEL'])


async def get_api_key(
        api_key_header: str = Security(api_key_header),
):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Key not present"
        )


@app.get('/api/healthcheck', status_code=200)
async def healthcheck():
    return 'Ready'


@app.post('/api/extraction')
def extract(values: Values, api_key: APIKey = Depends(get_api_key)):
    body = values.dict()
    if not body:
        return 'Expected text within body of request. No text found.', status.HTTP_400_BAD_REQUEST
    else:
        return extractor.go_extract(body, summarizer_model=summarizer_model.model,
                                    tokenizer=summarizer_model.tokenizer,
                                    max_length=int(os.environ['MAX_LENGTH']),
                                    num_beams=int(os.environ['NUM_BEAMS']))


# Remove these two lines below for non-debug/production mode
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
