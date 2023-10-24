import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from urllib.parse import unquote
import configparser

from modules.sql import add_message, read_thread
from modules.utils import *


config = configparser.ConfigParser()                                     
config.read('config.ini')

token = config.get('TELEGRAM', 'BOT_TOKEN')
cookie = config.get('BING', 'COOKIE')

# Initialize bot and dispatcher
bot = Bot(token=token)
dp = Dispatcher()


@dp.message(Command("start"))
# This function sends a welcoming message when the bot starts
async def cmd_start(message: types.Message):
    await message.answer("Hello! Main features:\n- Threaded ChatGPT bot using Bing: The bot maintains isolated threads of messages, allowing for separate conversations to be held concurrently.\n- Image Generation: The bot generates images using the Dalle library. Images can be generated by using the /image command or by providing a prompt in a message.\n- Conversation Management: The bot maintains a conversation thread in a SQLite database, allowing for persistent and organized conversations.")


@dp.message(Command("image"))
# Generate image using the provided prompt
async def def_image(message: types.Message):

    # Get the actual prompt by removing the command part from the message
    prompt = message.text.split('/image ')[1]

    # Generate image URL
    urls = await generate_image(bot, prompt)

    # Reply with the generated image
    await reply_with_images(bot, message, urls)


@dp.message()
# Main function that processes all non-command messages
async def maindef(message: types.Message):

    # Download image and get the prompt
    image, prompt = await download_image(bot, message)

    
    # Attempt to get the thread_id from the reply_to_message. If it fails (meaning the message is not a reply), then treat the thread_id as the message_id of this message itself.
    try:
        thread_id = str(message.reply_to_message.message_id)
    except:
        thread_id = str(message.message_id)

    # Answer to the message
    reply = await message.answer(to_html('Generating...'), reply_to_message_id=message.message_id, parse_mode='HTML')

    # Add the message to the database
    add_message(thread_id=thread_id, role='user', content=prompt)

    # Read the thread from the database
    messages = read_thread(thread_id=thread_id)

    # Generate a message using the thread and image
    generated_message = await generate_message(messages, image)

    if 'https://www.bing.com/images/create?q=' in generated_message:
        # If a new image URL is generated, generate a new image
        prompt = generated_message.split('https://www.bing.com/images/create?q=')[1]
        prompt = unquote(prompt)
        urls = await generate_image(prompt)
        await reply_with_images(bot, message, urls)

        # Delete the 'Generating...' message
        await reply.delete()

    else:
        # Update message with the generated message
        await reply.edit_text(generated_message, parse_mode='HTML')

    # Add the message to the database with the role 'assistant'
    add_message(thread_id=thread_id, role='assistant', content=generated_message)

    # Debugging purpose print statement to display the thread
    print(read_thread(thread_id=thread_id))


# Main function that starts the bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())