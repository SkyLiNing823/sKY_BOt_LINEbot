# import pyimgur
# CLIENT_ID = "14dcbae49ad6b84"
# title = "Uploaded with PyImgur"
# im = pyimgur.Imgur(CLIENT_ID)
# uploaded_image = im.upload_image('a.jpg', title=title)
# print(uploaded_image.link)

import datetime
import pytz
TW_tz = pytz.timezone('Asia/Taipei')
time = datetime.datetime.now(TW_tz).strftime('%Y-%m-%d %H:%M:%S')
print(datetime.datetime.now(TW_tz).strftime('%Y-%m-%d %H:%M:%S'))
