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


def get_info(event):
    user_id = event.source.user_id
    admin = 'U2290158f54f16aea8c2bdb597a54ff9e'
    group_id = getattr(event.source, 'group_id', 'N/A')
    main_group = 'C0862e003396d3da93b9016d848560f29'

    if group_id != 'N/A':
        profile = line_bot_api.get_group_member_profile(group_id, user_id)
    else:
        profile = line_bot_api.get_profile(user_id)

    user_name = profile.display_name
    user_pic_url = profile.picture_url
    user_status = profile.status_message

    # Send To Command Line
    print(f'{user_name} {user_id}')

    return user_id, user_name, user_pic_url, user_status, admin, group_id, main_group


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(sendTime())

    get_message = event.message.text.strip().rstrip().replace('！', '!')
    splited_message = get_message.split()

    user_id, user_name, user_pic_url, user_status, admin, group_id, main_group = get_info(
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
        '!img': lambda: uploadIMG(f"{user_id}.png"),
        '!pic': lambda: text_reply(uploadIMG(f"{user_id}.png"), event),
        '!sta': lambda: F_statistic(event),
        '!profile': lambda: text_reply(f'Name:\n{user_name}\n\nID:\n{user_id}\n\nPic URL:\n{user_pic_url}\n\nStatus:\n{user_status}', event),
        '@bot': lambda: F_LLM(get_message, event),
    }

    cmd = splited_message[0].lower() if splited_message else ''

    asyncio.create_task(F_async_countMSG())

    if user_id == admin:
        if cmd == '!resp':
            F_respManager(splited_message, event)

    if cmd in command_handlers:
        command_handlers[cmd]()

    elif get_message[:2] == '!抽':
        F_lottery(group_id, splited_message, event)

    elif get_message[-4:].lower() in ['.jpg', '.png']:
        F_imgSearch(splited_message, jdata, get_message, event)

    elif get_message[:4] == '有人知道' or (get_message[:1] == '教' and get_message[-1:] == '嗎' and len(get_message) > 2):
        F_GoogleSearch(get_message, event)

    elif 'https"//' in get_message:
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

    else:
        if '機器人' in get_message:
            for i in jdata['abuse_words']:
                if i in get_message:
                    L = ['兇三小 幹', '家裡死人嗎？', '是在叫三小', '靠北啥？']
                    word = random.choice(L)
                    text_reply(user_name+word, event)
            for i in jdata['praise_words']:
                if i in get_message:
                    img_reply(
                        'https://memeprod.sgp1.digitaloceanspaces.com/meme/64f9c2b295e72175fdebec660914abd6.png', event)

        for i in jdata['echo_words']:
            if i in get_message:
                if get_message[0] == '我':
                    get_message = get_message.replace('我', '你')
                if "不會" not in get_message:
                    get_message = get_message.replace('會', '才會')
                if "會不會" not in get_message:
                    get_message = get_message.replace('會不會', '才會')
                if "你是" in get_message or "妳是" in get_message:
                    get_message = get_message.replace('是', '才是')
                    get_message = get_message.replace('才是不才是', '才是')
                text_reply(get_message, event)
                break

        for i in jdata['full_echo_words']:
            if i == get_message:
                text_reply(get_message, event)
                break

        if '買' in get_message:
            if '會員' in get_message:
                text_reply('買 我叫你買', event)

        if '我' in get_message:
            if '不會' in get_message and len(get_message) < 20:
                L = ['哈哈你又不會了', '你要確定ㄋㄟ', '真假', '喔是喔，真的假的，55555', '好了啦']
                word = random.choice(L)
                text_reply(word, event)

        if '我寶寶' in get_message:
            L = ['恩', '喔是喔，真的假的，55555', 'ㄏ', '好了啦', '多出去走走', '有點可憐', '啊哈哈']
            word = random.choice(L)
            text_reply(word, event)
        if '教嗎' in get_message or '教嘛' in get_message or '教？' in get_message or '教?' in get_message:
            text_reply('不要嘲諷好嗎', event)

        if '加推' in get_message or '我婆' in get_message:
            text_reply('又？', event)

        if '一生' in get_message and '推' in get_message and '不' not in get_message:
            text_reply(user_name+'你真可憐', event)

    # if Message_counter == 3:
    #     text_reply(Message_container, event)

    sheet, resp_names, resp_p, resp_words = resp_reload()

    if user_name in resp_names:
        p = resp_p[resp_names.index(user_name)]
        words = resp_words[resp_names.index(user_name)]
        resp(int(p), words, event)

    with open('previous_user_name.txt', 'w') as f:
        f.write(user_name)


@handler.add(MessageEvent, message=AudioMessage)
def handle_message_Audio(event):
    sound2text(event)


@handler.add(MessageEvent, message=ImageMessage)
def handle_message_Image(event):
    imgSave(event)


@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
