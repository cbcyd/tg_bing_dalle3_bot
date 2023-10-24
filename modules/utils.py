import re
import base64
import logging
import time
import configparser

from aiogram import types
from aiogram.utils.media_group import MediaGroupBuilder
from dalle3 import Dalle
import g4f

# Read Bing cookie from config.ini
config = configparser.ConfigParser()                                     
config.read('config.ini')
cookie = config.get('BING', 'COOKIE')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create Dalle instance
dalle = Dalle(cookie)

# Regex for code and hyperlink replacement
code_re = re.compile(r"^`(.+?)`$", re.MULTILINE)
pre_re = re.compile(r"^```(.+?)```$", re.MULTILINE | re.DOTALL)
pattern = r'\[(.*?)\]\((.*?)\)'
replacement = r'<a href="\2">\1</a>'

# Function for conversion of byte data to base64
def bytes_to_data(data):
    data = data.read()
    data64 = u''.join(map(chr, base64.b64encode(data)))
    return u'data:image/png;base64,%s' % (data64)

# Function to convert string to HTML text
def to_html(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = pre_re.sub(r"<pre>\1</pre>", text)
    text = code_re.sub(r"<code>\1</code>", text)
    text = re.sub(pattern, replacement, text)
    return text

# Function responds with images in Telegram bot
async def reply_with_images(bot, incoming_msg: types.Message, urls):
    media = MediaGroupBuilder()
    for url in urls:
        media.add_photo(media=url, caption=url)
    await bot.send_media_group(chat_id=incoming_msg.chat.id, media=media.build(), reply_to_message_id=incoming_msg.message_id)

# Function prompts to generate image using Dalle
async def generate_image(prompt):
    dalle.create(prompt)
    urls = dalle.get_urls()
    print(f'Generated: {prompt}')
    return urls

# Function downloads and formats image accordingly
async def download_image(bot, message):
    if message.photo:
        file_id = message.photo[-2].file_id
        file = await bot.get_file(file_id)
        data = await bot.download_file(file.file_path)
        image = bytes_to_data(data)
        prompt = message.caption
    else:
        image = None
        prompt = message.text
    return image, prompt

# Function generates message using Bing
async def generate_message(messages, image):
    response = g4f.ChatCompletion.create(
        model=g4f.models.default,
        messages=messages,
        provider=g4f.Provider.Bing,
        stream=True,
        image = image
    )
    message = ''
    for i in response:
        message = message + i
        print(i, flush=True, end='')
    message = to_html(message)
    return message