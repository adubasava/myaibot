
from config import settings
from aiogram import Bot, F, Router
from aiogram.types import Message, File, FSInputFile
from aiogram.filters import CommandStart
import openai
from openai import OpenAI
from pathlib import Path
import whisper
import os
import requests
import subprocess
import time

TELEGRAM_BOT_API_TOKEN=settings.telegram_bot_api_token
openai.api_key = os.getenv("OPENAI_API_KEY")

router = Router()
client = OpenAI()


async def ask_assistant(question: str):
    assistant = client.beta.assistants.create(
    name="General Assistant",
    instructions="You are a personal assistant. Answer questions briefly, in a sentence or less.",
    model="gpt-4-1106-preview",
    )

    thread = client.beta.threads.create()

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question,
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )


    def wait_on_run(run, thread):
        while run.status == "queued" or run.status == "in_progress":
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
            time.sleep(0.5)
        return run

    wait_on_run(run, thread)

    messages = client.beta.threads.messages.list(
        thread_id=thread.id, order="asc", after=message.id
    )

    def get_response(thread):
        return client.beta.threads.messages.list(thread_id=thread.id, order="asc")

    def process_reply(messages):
        reply = ""
        for m in messages:
            if m.role == 'assistant':
                reply = reply + m.content[0].text.value
        return reply

    reply = process_reply(get_response(thread))

    return reply


async def get_text_from_voice(file: File, file_name: str):    
    with open(file_name+'.oga', 'wb') as f:
        f.write(file.content) 
    subprocess.run(['ffmpeg', '-i', file_name+'.oga', file_name+'.mp3'])    
    model = whisper.load_model("small")
    result = model.transcribe(file_name+'.mp3')
    return result["text"]


async def get_openai_response(prompt, file_name):
    file = 'response_'+file_name+'.mp3'
    response_text = await ask_assistant(prompt)

    speech_file_path = Path(__file__).parent / file
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=response_text
    )

    response.stream_to_file(speech_file_path)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Я умею принимать голосовые сообщения, \
                         преобразовывать их в текст, получать и озвучивать ответы на заданные вопросы.")
    await message.answer("Присылай вопрос в виде голосового сообщения")


@router.message(F.content_type == "voice")
async def process_voice_message(message: Message, bot: Bot):    
    reaction = await message.answer("Идёт распознавание...")
    file_info = await bot.get_file(message.voice.file_id)
    file_name = os.path.basename(file_info.file_path)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(TELEGRAM_BOT_API_TOKEN, file_info.file_path)) 
    
    prompt = await get_text_from_voice(file, file_name)   
    await get_openai_response(prompt, file_name)

    response_audio = f"response_{file_name}.mp3"
    
    await message.reply_voice(voice=FSInputFile(response_audio), caption="Ответ ИИ")
    await reaction.edit_text("Готово!")
    
    os.remove(file_name+'.mp3')
    os.remove(file_name+'.oga')
    os.remove(response_audio)