from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import PlainTextResponse
from linebot.exceptions import InvalidSignatureError
from utils import handler
from handlers import *



app = FastAPI()

@app.get('/')
async def health_check():
    return {'status': 'Healthy'}

@app.post('/')
async def callback(request: Request, x_line_signature:str = Header(None)):
    body = await request.body()
    body_text = body.decode("utf-8")
    try:
        handler.handle(body_text, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail='Invalid signature')
    return PlainTextResponse('OK')

initialization()

