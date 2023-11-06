import re
import base64
import logging
import time
import configparser
import markdown
import html
from bleach import clean
from bs4 import BeautifulSoup, NavigableString
import io

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, InlineQueryHandler, MessageHandler, filters

from dalle3 import Dalle
import g4f

import nest_asyncio
nest_asyncio.apply()

# Read Bing cookie from config.ini
config = configparser.ConfigParser()                                     
config.read('config.ini')
cookie = config.get('BING', 'COOKIE')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create Dalle instance
dalle = Dalle(cookie)

# Function for conversion of byte data to base64
def bytes_to_data(data):
    data.seek(0)
    data = data.read()
    data64 = u''.join(map(chr, base64.b64encode(data)))
    return u'data:image/png;base64,%s' % (data64)

def split_text(text, max_length=4096):
    soup = BeautifulSoup(text, 'html.parser')

    blocks = []
    current_block = ''

    for element in soup:
        #print(element)
        #print('#############s')
        if isinstance(element, NavigableString):
            # This is a non-<code> block
            element = str(element)
            while len(element) > 0:
                if len(current_block) + len(element) <= max_length:
                    # The entire element can fit in the current block
                    current_block += element
                    element = ''
                else:
                    # Only part of the element can fit in the current block
                    space_left = max_length - len(current_block)
                    current_block += element[:space_left]
                    blocks.append(current_block)
                    current_block = ''
                    element = element[space_left:]
        else:
            # This is a <code> block
            if len(current_block) > 0:
                # Finish the current block
                blocks.append(current_block)
                current_block = ''
            code = str(element)
            if len(code) > max_length:
                #print(code)
                splitted_text = []
                while len(code) > max_length:
                    batch = code[:max_length]
                    i = max_length - batch[::-1].index('\n')
                    if code[:i].startswith('<code>'):
                        splitted_text.append(f'{code[:i]}</code>')
                    elif code[:i].endswith('</code>'):
                        splitted_text.append(f'<code>{code[:i]}')
                    else:
                        splitted_text.append(f'<code>{code[:i]}</code>')
                    code = code[i:]
                if len(code):                    
                    if code[:i].startswith('<code>'):
                        splitted_text.append(f'{code[:i]}</code>')
                    elif code[:i].endswith('</code>'):
                        splitted_text.append(f'<code>{code[:i]}')
                    else:
                        splitted_text.append(f'<code>{code[:i]}</code>')
                blocks.extend(splitted_text)
                continue
                #raise ValueError('A <code> block is longer than the maximum block length')
            blocks.append(code)

    if len(current_block) > 0:
        # Finish the last block
        blocks.append(current_block)

    messages = ['']
    for block in blocks:
        if len(messages[-1])+len(block) < max_length:
            messages[-1] += block
        else: messages.append(block)

    return messages

def convert_markdown_to_telegram_html(markdown_text):
    html_text = markdown.markdown(markdown_text)
    allowed = ['i', 'b', 'u', 's', 'pre', 'code', 'a', 'span']
    html_text = clean(html_text, tags=allowed, strip=True, strip_comments=True)
    text = ''
    b = True
    for i in html_text.split("\n"):
        if "```" in i:
            text += "<code>\n" if b else "</code>\n"
            b = not b
        else: text = text + i + '\n'
    return text

# Function responds with images in Telegram bot
async def reply_with_images(message, urls, prompt):
    media = []
    #print(urls)
    if urls:
        for url in urls:
            media.append(InputMediaPhoto(media=url))#, caption=url))
        await message.reply_media_group(media=media, caption=prompt)
    else:
        print('URLS:', urls)
        await message.reply_text('Error, the request was probably blocked.')

# Function prompts to generate image using Dalle
def generate_image(prompt):
    try:
        dalle.create(prompt)
        urls = dalle.get_urls()
        print(f'Generated: {prompt}')
        return urls
    except:
        return False

# Function downloads and formats image accordingly
async def download_image(message):
    #print(message)
    if message.photo:
        file = await message.photo[-1].get_file()
        data = io.BytesIO()
        #print('photo:',file)
        #input()
        await file.download_to_memory(data)
        image = bytes_to_data(data)
        prompt = message.caption
    else:
        image = None
        prompt = message.text

    #print(image, prompt)
    return image, prompt

# Function generates message using Bing
async def generate_message(messages, image):
    
    response = await g4f.ChatCompletion.create_async(
        model=g4f.models.default,
        messages=messages,
        provider=g4f.Provider.Bing,
        #stream=True,
        image = image
    )
    #print(response)
    message = convert_markdown_to_telegram_html(response)
    #print(message)
    return message