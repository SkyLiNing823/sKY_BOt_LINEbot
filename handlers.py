from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (MessageEvent,
                            TextMessage,
                            AudioMessage,
                            ImageMessage,
                            TextSendMessage,
                            ImageSendMessage,
                            VideoSendMessage,
                            AudioSendMessage,
                            LocationSendMessage,
                            StickerSendMessage,
                            ImagemapSendMessage,
                            TemplateSendMessage,
                            FlexSendMessage,
                            ButtonsTemplate,
                            MessageTemplateAction,
                            PostbackEvent,
                            PostbackTemplateAction)
from utils import *


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(sendTime())

    get_message = event.message.text.strip().rstrip().replace('！', '!')
    splited_message = get_message.split()

    user_id, user_name, user_pic_url, user_status, admin, group_id, main_group = getInfo(
        event)

    with open('json/setting.json', 'r', encoding='utf8') as jfile:
        jdata = json.load(jfile)

    command_handlers = {
        '!t': lambda: F_translate(get_message, splited_message, event),
        '!抽': lambda: F_lottery(group_id, splited_message, event),
        '!yt': lambda: F_ytPreview(get_message, jdata, event),
        '!g': lambda: F_GoogleSearch(get_message, event),
        '!rand': lambda: F_randnum(get_message, event),
        '!rate': lambda: F_rate(get_message, send_headers, event),
        '!img': lambda: img_reply(upload2discord(f"{user_id}.png"), event),
        '!url': lambda: text_reply(upload2discord(f"{user_id}.png"), event),
        '!tts': lambda: F_TTS(get_message, event),
        '!sta': lambda: F_statistic(event),
        '!profile': lambda: text_reply(f'Name:\n{user_name}\n\nID:\n{user_id}\n\nPic URL:\n{user_pic_url}\n\nStatus:\n{user_status}', event),
        '!group': lambda: text_reply(f'Group ID:\n{group_id}\n\n', event),
        '@bot': lambda: F_LLM(get_message, user_name, group_id, True, event),
        '!bot': lambda: F_LLM(get_message, user_name, group_id, False, event),
    }

    cmd = splited_message[0].lower() if splited_message else ''

    asyncio.create_task(F_async_countMSG())

    if cmd in command_handlers:
        command_handlers[cmd]()

    elif get_message.lower() == 'hi':
        text_reply(get_message, event)

    elif get_message[:2] == '!抽':
        F_lottery(group_id, splited_message, event)

    elif splited_message[-1][-4:].lower() in ['.jpg', '.png'] or (len(splited_message) >= 2 and (splited_message[-2][-4:].lower() in ['.jpg', '.png'])):
        F_imgSearch(splited_message, jdata, get_message, event)

    elif 'https://' in get_message:
        if get_message[8:16] == 'youtu.be' or get_message[8:19] == 'www.youtube' or get_message[8:17] == 'm.youtube':
            F_ytPreview(get_message, jdata, event)

        elif 'ptt' in get_message:
            F_pttPreview(get_message, event)

        elif 'x.com' in get_message:
            F_twitterPreview(get_message, event)

        elif 'forum.gamer.com.tw' in get_message:
            F_bahamutePreview(get_message, event)

        elif 'home.gamer.com.tw' in get_message:
            F_bahamuteHomePreview(get_message, event)

    elif get_message[0].isdigit() and get_message[-1].isdigit():
        F_eval(get_message, event)


@handler.add(MessageEvent, message=AudioMessage)
def handle_message_Audio(event):
    sound2text(event)


@handler.add(MessageEvent, message=ImageMessage)
def handle_message_Image(event):
    saveIMG(event)


@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
