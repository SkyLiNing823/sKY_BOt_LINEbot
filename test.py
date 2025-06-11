import pyimgur
CLIENT_ID = "14dcbae49ad6b84"
title = "Uploaded with PyImgur"
im = pyimgur.Imgur(CLIENT_ID)
uploaded_image = im.upload_image('a.jpg', title=title)
print(uploaded_image.link)
