import os
import json
import copy
import os
import datetime
import requests
import random
from math import *
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from google import genai
from gtts import gTTS
import langid
import googletrans
from googlesearch import search
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
import speech_recognition as sr
import matplotlib.pyplot as plt
from pydub import AudioSegment
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from PIL import Image
import audioread
# import numpy as np
# import cv2

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (MessageEvent,
                            TextMessage,
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


channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

send_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8"}

TW_tz = pytz.timezone('Asia/Taipei')

client_default = genai.Client(api_key=os.getenv('gemini_key_DEFAULT'))
chat_default = client_default.chats.create(model="gemini-2.0-flash")
client_playground = genai.Client(api_key=os.getenv('gemini_key_FOR_PLAYGROUD'))
chat_playground = client_playground.chats.create(model="gemini-2.0-flash")
client_lab = genai.Client(api_key=os.getenv('gemini_key_FOR_LAB'))
chat_lab = client_lab.chats.create(model="gemini-2.0-flash")


### general funcs ###

def initialization():
    # message = TextSendMessage(text='Bot restarted!')
    # line_bot_api.push_message('U2290158f54f16aea8c2bdb597a54ff9e', message)
    scheduler = BackgroundScheduler(timezone=TW_tz)
    scheduler.add_job(F_new_day_call, 'cron', hour=0, minute=0)
    scheduler.start()


def getInfo(event):
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


def line_reply(reply, event):
    LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
               ).reply_message(event.reply_token, reply)


def text_reply(content, event):
    reply = TextSendMessage(text=content)
    LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
               ).reply_message(event.reply_token, reply)


def rand_text_reply(n, content, event):
    randNum = random.randint(1, n)
    if randNum == 1:
        text_reply(content, event)


def img_reply(URL, event):
    reply = ImageSendMessage(
        original_content_url=URL, preview_image_url=URL)
    LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
               ).reply_message(event.reply_token, reply)


def audio_reply(URL, duration, event):
    reply = AudioSendMessage(
        original_content_url=URL, duration=duration)
    LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
               ).reply_message(event.reply_token, reply)


def video_reply(URL, URL2, event):
    reply = VideoSendMessage(
        original_content_url=URL, preview_image_url=URL2)
    LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
               ).reply_message(event.reply_token, reply)


def flex_reply(words, content, event):
    reply = FlexSendMessage(words, content)
    LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
               ).reply_message(
        event.reply_token, reply)


def sendTime(yesterday=False, format='%Y/%m/%d'):
    if yesterday:
        date = datetime.datetime.now(TW_tz) - datetime.timedelta(days=1)
        return date.strftime(format)
    return datetime.datetime.now(TW_tz).strftime(format)


def saveIMG(event):
    PATH = f'{event.source.user_id}.png'
    image_content = line_bot_api.get_message_content(event.message.id)
    with open(PATH, 'wb') as fd:
        for chunk in image_content.iter_content():
            fd.write(chunk)


def upload2discord(PATH):
    url = f"https://discord.com/api/v10/channels/{os.getenv('DISCORD_CHANNEL_ID')}/messages"
    headers = {
        "Authorization": f"Bot {os.getenv('DISCORD_BOT_TOKEN')}"
    }
    with open(PATH, 'rb') as f:
        files = {
            "file": (PATH, f)
        }
        response = requests.post(url, headers=headers, files=files)
    json_resp = response.json()
    return json_resp['attachments'][0]['url']


def sound2text(event):
    PATH = 'tmp.mp3'
    DST = 'tmp.wav'
    audio = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
                       ).get_message_content(event.message.id)
    with open(PATH, 'wb') as fd:
        for chunk in audio.iter_content():
            fd.write(chunk)
        fd.close()
    try:
        prompt = f'"Please transcribe the attached audio into a verbatim script. Only include the content of the audio—no additional text.'
        audio = client_default.files.upload(file=PATH)
        contents = [audio, prompt]
        response = client_default.models.generate_content(
            model="gemini-2.0-flash", contents=contents)
        text = response.text
    except:
        # converting
        sound = AudioSegment.from_file(PATH)
        sound.export(DST, format="wav")
        # recgonizing
        r = sr.Recognizer()
        with sr.AudioFile(DST) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language='zh-Hant')
        os.remove("tmp.wav")
    text_reply(text, event)


def reloadSheet(key):
    scopes = ["https://spreadsheets.google.com/feeds"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "json/credentials.json", scopes)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(key).sheet1
    return sheet


def F_statistic(event):
    sheet = reloadSheet("1ti_4scE5PyIzcH4s6mzaWaGqiIQfK9X_R--oDXqyJsA")
    data = sheet.get_all_values()
    X = [d[0][5:] for d in data[-7:]]
    Y = [int(d[1]) for d in data[-7:]]
    plt.plot(X, Y)
    plt.title("Message Counting(only text)")
    for a, b in zip(X, Y):
        plt.text(a, b, b, ha='center', va='bottom', fontsize=12)
    plt.savefig("tmp.jpg")
    PATH = "tmp.jpg"
    link = upload2discord(PATH)
    img_reply(link, event)


def F_countMSG():
    try:
        sheet = reloadSheet("1ti_4scE5PyIzcH4s6mzaWaGqiIQfK9X_R--oDXqyJsA")
        data = sheet.get_all_values()
        dates = [data[i][0]for i in range(len(data))]
        times = [data[i][1]for i in range(len(data))]
        dt = sendTime()
        if len(dates) == 0 or dt != dates[-1]:
            sheet.append_row([dt, '1'])
        else:
            n = int(times[dates.index(dt)])
            sheet.update_cell(dates.index(dt)+1, 2, str(n+1))
    except:
        pass


async def F_async_countMSG():
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, F_countMSG)


def F_translate(get_message, splited_message, event):
    translator = googletrans.Translator()
    text = get_message[3:]
    if text == '?':
        trans = str(googletrans.LANGCODES)[1:-1].replace(', ', '\n')
    elif splited_message[1] in googletrans.LANGCODES.values() and len(splited_message) != 2:
        text = get_message[6:]
        trans = translator.translate(text, dest=splited_message[1]).text
    else:
        trans = translator.translate(text, dest='zh-tw').text
    text_reply(trans, event)


def F_TTS(get_message, event):
    LANG, _ = langid.classify(get_message[5:])
    tts = gTTS(text=get_message[5:], lang=LANG)
    tts.save("tmp.wav")
    with audioread.audio_open('tmp.wav') as f:
        duration = int(f.duration) * 1000
    URL = upload2discord('tmp.wav')
    audio_reply(URL, duration, event)


def F_eval(get_message, event):
    operator = ['+', '-', '*', '/', '%', '.', '(', ')', ' ']
    test = get_message
    for i in operator:
        test = test.replace(i, '')
    if test.isdigit() and get_message.isdigit() == False:
        content = str(round(eval(get_message), 4))
        text_reply(content, event)
    else:
        return


def F_lottery(group_id, splited_message, event):
    if group_id == "C0862e003396d3da93b9016d848560f29":
        sheet = reloadSheet("1EfgW0_aNkc_r790Htp3NTmhSRfHuriil1u0YZhPYrAo")
        memberData = sheet.get_all_values()
        member_list = [memberData[i][0]
                       for i in range(len(memberData))]
        if len(splited_message) == 1:
            name = random.choice(member_list)
            text_reply(f'{name}', event)
        elif len(splited_message) == 2 and splited_message[1].isdigit():
            count = int(splited_message[1])
            count = min(count, len(member_list))
            selected_names = random.sample(member_list, count)
            content = '\n'.join(selected_names)
            text_reply(content, event)
        elif splited_message[1] == 'list':
            content = '\n'.join(member_list)
            text_reply(content, event)
        elif splited_message[1] == '+':
            if splited_message[2] not in member_list:
                sheet.append_row([splited_message[2]])
                member_list.append(splited_message[2])
                text_reply(f'已將{splited_message[2]}登錄成員名單', event)
            else:
                text_reply(f'{splited_message[2]}已在成員名單', event)
        elif splited_message[1] == '-':
            if splited_message[2] not in member_list:
                text_reply(f'成員名單不存在{splited_message[2]}', event)
            else:
                member_list.remove(splited_message[2])
                for i in range(len(member_list)):
                    sheet.update_cell(i+1, 1, member_list[i])
                sheet.update_cell(len(member_list)+1, 1, '')
                text_reply(f'已將{splited_message[2]}於成員名單刪除', event)
    else:
        text_reply('不可於此處抽選', event)


def F_imgSearch(splited_message, jdata, get_message, event):
    if splited_message[-1].isdigit():
        n = min(int(splited_message[-1]), 10)
        get_message = get_message[:-len(splited_message[-1])]
    else:
        n = 1
    URL_list = []
    params = {
        "engine": "google",
        "tbm": "isch"
    }
    params['q'] = get_message[:-4]
    while True:
        params['api_key'] = random.choice(jdata['serpapi_key'])
        client = GoogleSearch(params)
        data = client.get_dict()
        if 'error' not in data.keys():
            break
    imgs = data['images_results']
    n = min(n, len(imgs))
    for img in imgs:
        if len(URL_list) == n:
            break
        if img['original'][:5] == 'https' and img['original'][-4:] in ['.jpg', '.png', 'jpeg']:
            URL_list.append(img['original'])

    with open('json/imgBubble.json', 'r', encoding='utf8') as jfile:
        jdata = json.load(jfile)
    ctn = []
    for i in range(n):
        tmp = copy.deepcopy(jdata)
        tmp['hero']['url'] = tmp['hero']['action']['uri'] = URL_list[i]
        ctn.append(tmp)
    if len(ctn) > 1:
        with open('json/carousel.json', 'r', encoding='utf8') as jfile:
            jdataCtn = json.load(jfile)
        jdataCtn['contents'] = ctn
        reply = jdataCtn
        flex_reply('imgs', reply, event)
    else:
        img_reply(ctn[0]['hero']['url'], event)


def F_ytSearch(splited_message, get_message, jdata, event):
    if splited_message[-1].isdigit():
        x = int(splited_message[-1])
        q = get_message[4:-2]
    else:
        x = 3
        q = get_message[4:]
    URL = ''
    YOUTUBE_API_KEY = jdata['YOUTUBE_API_KEY']
    url = 'https://www.googleapis.com/youtube/v3/search?part=snippet&q=' + \
        q+'&key='+YOUTUBE_API_KEY+'&type=video&maxResults='+str(x)
    request = requests.get(url)
    data = request.json()
    for i in range(x):
        URL += 'https://www.youtube.com/watch?v=' + \
            data['items'][i]['id']['videoId']+'\n'
    text_reply(URL, event)


def F_GoogleSearch(get_message, event):
    text = ''
    query = get_message[2:]
    for url in search(query, num_results=3):
        if url not in text:
            text += url+'\n\n'
    text_reply(text, event)


# def F_tmr(send_headers, splited_message, event):
#     data = {
#         'idpwLgid': os.getenv('SMA_ID', None),
#         'idpwLgpw': os.getenv('SMA_PW', None),
#         'my_prevtyp': 'S',
#         'my_prevdom': 'smavoice.jp',
#         'my_prevurl': '/s/sma03/artist/45/contents',
#         'my_prevmet': 'GET',
#         'my_webckid': '79666726243d1f7e073d7d3b90e48ebd6da66176',
#         'my_prevprm': '{"ct":"45_122_02","tp":"122","arti":"45","cd":"45"}',
#         'mode': 'LOGIN',
#         'ima': 3340

#     }
#     url = 'https://smavoice.jp/s/sma03/login'
#     session = requests.Session()
#     session.post(url, headers=send_headers, data=data)
#     URL = []
#     response = session.get(
#         'https://smavoice.jp/s/sma03/artist/45/contents?ima=4940&ct=45_122_02&tp=122&arti=45', headers=send_headers)
#     html = response.content
#     bsObj = BeautifulSoup(html, 'html.parser')
#     shouter = bsObj.findAll('img', {'class': 'nocover'})
#     try:
#         limit = int(splited_message[1])
#     except:
#         limit = 10000
#     count = 0
#     for i in shouter:
#         if count == limit:
#             break
#         URL.append('https://smavoice.jp'+i['src'])
#         count += 1
#     if (splited_message[1].isdigit()):
#         text = ''
#         for i in URL:
#             text += i+'\n'
#         text_reply(text, event)
#     else:
#         index = int(splited_message[1][1:])
#         if index > len(URL):
#             index = len(URL)
#         text_reply(URL[index-1], event)


def F_ytPreview(get_message, jdata, event):
    YOUTUBE_API_KEY = jdata['YOUTUBE_API_KEY']
    if get_message[:17] == 'https://youtu.be/':
        id = get_message[17:get_message.index('?')].rstrip()
    elif get_message[:24] == 'https://www.youtube.com/':
        id = get_message[32:get_message.index('?')].rstrip()
    elif get_message[:22] == "https://m.youtube.com/":
        id = get_message[30:get_message.index('?')].rstrip()
    print(id)
    URL = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id=' + \
        id+'&key='+YOUTUBE_API_KEY
    request = requests.get(URL)
    data = request.json()
    title = data['items'][0]['snippet']['title']
    channel = data['items'][0]['snippet']['channelTitle']
    view = data['items'][0]['statistics']['viewCount']
    try:
        like = data['items'][0]['statistics']['likeCount']
    except:
        like = 'N/A'
    try:
        dislike = data['items'][0]['statistics']['dislikeCount']
    except:
        dislike = 'N/A'
    try:
        comment = data['items'][0]['statistics']['commentCount']
    except:
        comment = 'N/A'
    channelId = data['items'][0]['snippet']['channelId']
    URL2 = 'https://www.googleapis.com/youtube/v3/channels?part=statistics&id=' + \
        channelId+'&key='+YOUTUBE_API_KEY
    request = requests.get(URL2)
    data = request.json()
    try:
        sub = data['items'][0]['statistics']['subscriberCount']
    except:
        sub = 'N/A'
    text = title+'\n' + \
        '-'+'\n' +\
        '<頻道資訊>\n' +\
        channel+'\n' +\
        '訂閱數: '+str(sub)+'\n'
    '-'+'\n' +\
        '<影片資訊>\n' +\
        '觀看數: '+str(view)+'\n' +\
        '讚數: '+str(like)+'    倒讚數: '+str(dislike)+'\n' +\
        '留言數: '+str(comment)+'\n'
    text_reply(text, event)


def F_pttPreview(get_message, event):
    start = get_message.find('http')
    end = get_message.find('.html')
    URL = get_message[start:end+5]
    payload = {
        'from': '/bbs/Gossiping/index.html',
        'yes': 'yes'
    }
    rs = requests.session()
    request = rs.post('https://www.ptt.cc/ask/over18', data=payload)
    request = rs.get(URL)
    html = request.text
    bsObj = BeautifulSoup(html, 'html.parser')
    shouter = bsObj.findAll('span', 'article-meta-value')
    author = shouter[0].text
    title = shouter[2].text
    main_container = bsObj.find(id='main-container')
    all_text = main_container.text
    if '留言' in get_message:
        pre_comment = all_text.split('批踢踢實業坊(ptt.cc)')[1]
        pre_comment_list = pre_comment.split('html')[1:]
        pre_comment = ''.join(pre_comment_list)
        pre_comment_list = pre_comment.split('\n')
        text = '\n\n'.join(pre_comment_list)
    else:
        pre_text = all_text.split('批踢踢實業坊(ptt.cc)')[0]
        pre_text = pre_text.split('\n--\n')[0]
        texts = pre_text.split('\n')
        contents = texts[2:]
        content = '\n'.join(contents)
        text = title + '\n' + '作者: '+author + '\n' + '-'+'\n' + content
    if len(text) > 5000:
        text = text[:5000]
    text_reply(text, event)


def F_twitterPreview(get_message, event):
    stack = []
    msg = []
    ctn = []
    with open('twitterStack.txt', 'a') as f:
        f.write(get_message+'\n')
    with open('twitterStack.txt', 'r') as f:
        for line in f.readlines():
            stack.append(line)
    for link in stack:
        url = 'https://tweetpik.com/api/v2/tweets?url='+link
        request = requests.get(url)
        contents = request.text
        if "avatarUrl" in contents:
            username = contents[contents.find(
                '<span class=\\"css-901oao css-16my406 css-1hf3ou5 r-poiln3 r-bcqeeo r-qvutc0\\"><span class=\\"css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0\\">')+len('<span class=\\"css-901oao css-16my406 css-1hf3ou5 r-poiln3 r-bcqeeo r-qvutc0\\"><span class=\\"css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0\\">'):contents.find('</span>')]
            screen_name = contents[contents.find(
                '"handler":"')+len('"handler":"'):contents.find('","avatarUrl":"')]
            if '.jpg' in contents:
                profile_image_url = contents[contents.find(
                    '","avatarUrl":"')+len('","avatarUrl":"'):contents.find('.jpg')+4]
            else:
                profile_image_url = contents[contents.find(
                    '","avatarUrl":"')+len('","avatarUrl":"'):contents.find('.png')+4]
            if 'https' not in profile_image_url:
                profile_image_url = 'https://upload.wikimedia.org/wikipedia/commons/5/50/Black_colour.jpg'
            if 'textHtml' in contents:
                tweet_text_HTML = contents[contents.find(
                    '"textHtml":"')+len('"textHtml":"'):contents.find('","verified"')]
                bsObj = BeautifulSoup(tweet_text_HTML, 'html.parser')
                tweet_text = ''
                for i in bsObj:
                    tweet_text += i.text
                tweet_text = tweet_text.replace('\\n', '\n')
            else:
                tweet_text = ' '
            retweet_count = str(contents[contents.find(
                '"retweets":')+len('"retweets":'):contents.find(',"replies"')])
            if retweet_count == 'null':
                retweet_count = '0'
            favorite_count = str(contents[contents.find(
                ',"likes":')+len(',"likes":'):contents.find(',"retweets":')])
            if favorite_count == 'null':
                favorite_count = '0'
            with open('json/twitterBubble.json', 'r', encoding='utf8') as jfile:
                jdata1 = json.load(jfile)
            jdata1['body']['contents'][0]['url'] = profile_image_url
            jdata1['body']['contents'][1]['text'] = username
            jdata1['body']['contents'][2]['text'] = screen_name
            jdata1['body']['contents'][4]['contents'][0]['text'] = tweet_text
            jdata1['body']['contents'][4]['contents'][2]['contents'][1]['text'] = retweet_count
            jdata1['body']['contents'][4]['contents'][3]['contents'][1]['text'] = favorite_count
            photos_urls = contents[contents.find(
                '"photos":[')+len('"photos":['):contents.find('],"videos"')].split(',')
            msg.append(FlexSendMessage('tweet', jdata1))
            if photos_urls[0] != '':
                with open('json/imgBubble.json', 'r', encoding='utf8') as jfile:
                    jdata2 = json.load(jfile)
                for i in range(len(photos_urls)):
                    tmp = copy.deepcopy(jdata2)
                    if 'jpg' in photos_urls[i]:
                        img_url = photos_urls[i][1:photos_urls[i].find(
                            '?')]+'.jpg'
                    else:
                        img_url = photos_urls[i][1:photos_urls[i].find(
                            '?')]+'.png'
                    print(img_url)
                    if 'https' in img_url:
                        tmp['hero']['url'] = tmp['hero']['action']['uri'] = img_url
                        ctn.append(tmp)
                        url = img_url
                if len(ctn) > 1:
                    with open('json/carousel.json', 'r', encoding='utf8') as jfile:
                        jdata = json.load(jfile)
                    jdata['contents'] = ctn
                    reply = jdata
                    msg.append(FlexSendMessage('tweet', reply))
                elif len(ctn) == 1:
                    msg.append(ImageSendMessage(
                        original_content_url=img_url, preview_image_url=img_url))
            else:
                p = {'url': get_message}
                r = requests.post(
                    'https://www.expertsphp.com/instagram-reels-downloader.php', data=p)
                html = r.content
                bsObj = BeautifulSoup(html, 'html.parser')
                if 'mp4' in r.text:
                    videos = bsObj.findAll(
                        'a', {'class': 'btn-sm'})
                    max_resolution = 0
                    for video in videos:
                        if 'mp4' in video['href']:
                            resolution = eval(video['href'].split(
                                '/')[-2].replace('x', '*'))
                            if resolution > max_resolution:
                                video_url = video['href']
                                max_resolution = resolution
                        else:
                            img_url = video['href']
                    msg.append(VideoSendMessage(
                        original_content_url=video_url, preview_image_url=img_url))
                else:
                    imgs = bsObj.findAll('img', {'alt': 'Thumbnail'})
                    for img in imgs:
                        img_url = img['src']
                    msg.append(ImageSendMessage(
                        original_content_url=img_url, preview_image_url=img_url))
        else:
            p = {'url': get_message}
            r = requests.post(
                'https://www.expertsphp.com/instagram-reels-downloader.php', data=p)
            html = r.content
            bsObj = BeautifulSoup(html, 'html.parser')
            with open('json/twitterBubble.json', 'r', encoding='utf8') as jfile:
                jdata1 = json.load(jfile)
            if 'mp4' in r.text:
                videos = bsObj.findAll(
                    'a', {'class': 'btn-sm'})
                for video in videos:
                    if 'mp4' in video['href']:
                        video_url = video['href']
                    else:
                        img_url = video['href']
                msg.append(VideoSendMessage(
                    original_content_url=video_url, preview_image_url=img_url))
            else:
                imgs = bsObj.findAll('img', {'alt': 'Thumbnail'})
                for img in imgs:
                    content = img['title']
                    img_url = img['src']
                jdata1['body']['contents'][0]['url'] = 'https://cdn.discordapp.com/attachments/856516846144192543/1102493248120963153/R-18_icon.svg.png'
                jdata1['body']['contents'][1]['text'] = '@' + \
                    get_message.split('/')[-3]
                jdata1['body']['contents'][2][
                    'text'] = '(Only the first image will be showed)'
                jdata1['body']['contents'][4]['contents'][0]['text'] = content
                jdata1['body']['contents'][4]['contents'][2]['contents'][1]['text'] = 'N/A'
                jdata1['body']['contents'][4]['contents'][3]['contents'][1]['text'] = 'N/A'
                msg.append(FlexSendMessage('tweet', jdata1))
                msg.append(ImageSendMessage(
                    original_content_url=img_url, preview_image_url=img_url))
    line_reply(msg, event)
    with open('twitterStack.txt', 'w') as f:
        f.write('')


def bahaLogin():
    rs = requests.session()
    data = {
        'uid': os.getenv('baha_UID', None),
        'passwd': os.getenv('baha_PW', None),
        'vcode': '7045'
    }
    rs.headers.update({
        'user-agent': 'Bahadroid (https://www.gamer.com.tw/)',
        'x-bahamut-app-instanceid': 'cc2zQIfDpg4',
        'x-bahamut-app-android': 'tw.com.gamer.android.activecenter',
        'x-bahamut-app-version': '251',
        'content-type': 'application/x-www-form-urlencoded',
        'content-length': '44',
        'accept-encoding': 'gzip',
        'cookie': 'ckAPP_VCODE=7045'
    })
    request = rs.post(
        'https://api.gamer.com.tw/mobile_app/user/v3/do_login.php', data=data)
    rs.headers = {
        'user-agent': 'Bahadroid (https://www.gamer.com.tw/)',
        'x-bahamut-app-instanceid': 'cc2zQIfDpg4',
        'x-bahamut-app-android': 'tw.com.gamer.android.activecenter',
        'x-bahamut-app-version': '251',
        'accept-encoding': 'gzip',
    }
    return rs


def F_bahamutePreview(get_message, event):
    rs = bahaLogin()
    request = rs.get(get_message)
    html = request.text
    html = html.replace('</div>', '\n</div>')
    bsObj = BeautifulSoup(html, 'html.parser')
    article = ''
    title = bsObj.findAll('h1', {'class': 'title'})[0].text
    username = bsObj.findAll('a', {'class': 'username'})[0].text
    uid = bsObj.findAll('a', {'class': 'userid'})[0].text
    gp = bsObj.findAll('a', {'class': 'tippy-gpbp-list'})[0].text
    bp = bsObj.findAll('a', {'class': 'tippy-gpbp-list'})[1].text
    article += '\n'+title+'\n\n'+'-'*len(title)+'\n\n'
    article += f'樓主: {username} {uid}\n\n推(GP): {gp}\n噓(BP): {bp}' + \
        '\n\n'+'-'*len(title)+'\n\n'
    text_reply(article, event)


def F_bahamuteHomePreview(get_message, event):
    rs = bahaLogin()
    request = rs.get(get_message)
    html = request.text
    html = html.replace('</div>', '\n</div>')
    bsObj = BeautifulSoup(html, 'html.parser')
    article = ''
    ctitle = bsObj.findAll(
        'h1', {'class': 'c-title'})[0].text.split(' ')
    date = f'{ctitle[0][2:]} {ctitle[1][:5]}'
    title = ctitle[1][5:]
    t = 2
    while t < len(ctitle):
        title += ' ' + ctitle[t]
        t += 1
    username = bsObj.findAll('p', {'class': 'gnn_man2'})[0].text[1:]
    rawCtn = bsObj.findAll('div', {'class': 'home_box'}
                           )[0]
    ctn = rawCtn.findAll('div')
    info = ctn[-1].text.split('\n')
    gp = info[1]
    collect = info[2]
    article += '\n'+f'{title}\n\n'+'------\n\n' + \
        f'{date}\n{username}\nGP: {gp}\n收藏: {collect}\n\n'
    last_url = []
    last_ctn = ''
    for row in ctn[:-1]:
        try:
            block = row.findAll('img', {'class': 'lazyload'})
            for url in block:
                if url not in last_url:
                    article += '\n'+url['data-src']+'\n'
                last_url.append(url)
        except:
            pass
        try:
            block = row.findAll('a', {'class': 'photoswipe-image'})
            for url in block:
                if url not in last_url:
                    article += '\n'+url['href']+'\n'
                last_url.append(url)
        except:
            pass
        try:
            url = row.find('iframe', {'class': 'lazyload'})['data-src']
            if url not in last_url:
                article += '\n'+url+'\n'
            last_url.append(url)
        except:
            pass
        if row.text != last_ctn:
            article += row.text
        last_ctn = row.text
    if len(article) > 5000:
        article = article[:5000]
    text_reply(article, event)


def F_randnum(get_message, event):
    content = list(map(int, get_message[6:].split()))
    if len(get_message[6:].split()) == 1:
        min = 0
        max = content[0]
        num = random.randint(min, max+1)
    else:
        num = ''
        choosed_list = []
        min = content[0]
        max = content[1]
        if len(get_message[6:].split()) == 2:
            times = 1
        elif len(get_message[6:].split()) == 3:
            times = content[2]
            if times > max - min:
                times = max - min
            elif times > 5000:
                times = 5000
        for i in range(times):
            rand = random.randint(min, max)
            while rand in choosed_list:
                rand = random.randint(min, max)
            choosed_list.append(rand)
            num += str(rand)
            if i != times-1:
                num += '\n'
    text_reply(num, event)


def F_rate(get_message, send_headers, event):
    money = get_message[6:]
    money = money.lower()
    data = ['usd', 'hkd', 'gbp', 'aud', 'cad', 'sgd', 'chf', 'jpy', 'zar',
            'sek', 'nzd', 'thb', 'php', 'idr', 'eur', 'krw', 'vnd', 'myr', 'cny']
    num = data.index(money)
    URL = 'https://rate.bot.com.tw/xrt?Lang=zh-TW'
    request = requests.get(URL, headers=send_headers)
    html = request.content
    bsObj = BeautifulSoup(html, 'html.parser')
    rate_table = bsObj.find('table', attrs={'title': '牌告匯率'}).find(
        'tbody').find_all('tr')
    buyin_rate = rate_table[num].find(
        'td', attrs={'data-table': '本行即期買入'})
    sellout_rate = rate_table[num].find(
        'td', attrs={'data-table': '本行即期賣出'})
    words = money.upper()+"\n即時即期買入: {}\n即時即期賣出: {}".format(buyin_rate.get_text().strip(),
                                                            sellout_rate.get_text().strip())
    text_reply(words, event)


# def F_faceDetect(event, id):
#     img = cv2.imread(f"{id}.png")
#     net = cv2.dnn.readNetFromCaffe(
#         "deploy.prototxt.txt", "res10_300x300_ssd_iter_140000.caffemodel")
#     h, w = img.shape[:2]
#     color = (0, 255, 0)
#     blob = cv2.dnn.blobFromImage(cv2.resize(
#         img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
#     net.setInput(blob)
#     detections = net.forward()
#     for i in range(0, detections.shape[2]):
#         confidence = detections[0, 0, i, 2]
#         if confidence < 0.5:
#             continue
#         box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
#         (startX, startY, endX, endY) = box.astype("int")
#         # text = "{:.2f}%".format(confidence * 100)
#         y = startY - 10 if startY - 10 > 10 else startY + 10
#         cv2.rectangle(img, (startX, startY), (endX, endY),
#                       color, 2)
#     grayImg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     face_classifier = cv2.CascadeClassifier(
#         cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
#     faceRects = face_classifier.detectMultiScale(grayImg, scaleFactor=1.3)
#     if len(faceRects):
#         for faceRect in faceRects:
#             x, y, w, h = faceRect
#             cv2.rectangle(img, (x, y), (x + h, y + w), color, 2)
#     cv2.imwrite("face.png", img)
#     img_reply(uploadIMG("face.png"), event)


def F_vote(event):
    reply = json.load(open('json/vote.json', 'r', encoding='utf-8'))
    flex_reply('vote', reply, event)


def F_LLM(get_message, user_name, group_id, memorization,  event):
    global client_default
    global client_playground
    global client_lab
    global chat_default
    global chat_playground
    global chat_lab
    key_table = {'Ce36c2b35e5459d427c3507ed40dc2112': [client_lab, chat_lab],
                 'C50ac0633ba25dc04ed18c9c0e46bdeab': [client_playground, chat_playground],
                 }

    if get_message[5:].lower() == 'reset':
        if group_id == 'Ce36c2b35e5459d427c3507ed40dc2112':
            chat_lab = client_lab.chats.create(model="gemini-2.0-flash")
        elif group_id == 'C50ac0633ba25dc04ed18c9c0e46bdeab':
            chat_playground = client_playground.chats.create(
                model="gemini-2.0-flash")
        else:
            chat_default = client_default.chats.create(
                model="gemini-2.0-flash")
        text_reply('已順利移除所有記憶。', event)
        return

    if group_id in key_table:
        client, chat = key_table[group_id]
    else:
        client, chat = client_default, chat_default

    prompt = f'speaker: {user_name} (DO NOT REPEAT THIS)\n-----\n' + \
        get_message[4:]

    if '圖片' in get_message[4:] or '照片' in get_message[4:] or 'image' in get_message[4:]:
        try:
            img = client.files.upload(file=f'{event.source.user_id}.png')
            contents = [img, prompt]
        except:
            text_reply('[Error] :  Cannot upload the image.', event)
    contents = prompt
    try:
        if memorization:
            response = chat.send_message(contents)
        else:
            response = client.models.generate_content(
                model="gemini-2.0-flash", contents=contents)
    except Exception as e:
        text_reply(f'[Error] : {str(e)}', event)
    reply = response.text
    if not reply:
        text_reply('[Error] :  The content is empty.', event)
    if len(reply) > 5000:
        reply = reply[:4970] + '\n---因內容超過5000字下略---'
    text_reply(reply, event)


### push func ###


def F_new_day_call():
    # leo = 'U0b1cfa976cedd1f86f45dac94988fd73'
    main_group = 'C0862e003396d3da93b9016d848560f29'
    # message = TextSendMessage(text='李俊賢你是甲')
    # line_bot_api.push_message(leo, message)

    now = sendTime()
    yesterday = sendTime(yesterday=True)
    sheet = reloadSheet("1ti_4scE5PyIzcH4s6mzaWaGqiIQfK9X_R--oDXqyJsA")
    data = sheet.get_all_values()
    times = 'N/A'
    for d in data[-2:]:
        if d[0] == yesterday:
            times = d[1]
    message = TextSendMessage(text=f'現在時間是{now}，昨天群組一共有{times}則訊息')
    line_bot_api.push_message(main_group, message)
