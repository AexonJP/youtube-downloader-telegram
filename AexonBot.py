import telebot
from pytube import YouTube
import ffmpeg
import os
from telebot import apihelper
from pytube.innertube import _default_clients
import re
remove_non_english = lambda s: re.sub(r'[^a-zA-Z\s\n\.]', ' ', s)
_default_clients["ANDROID_MUSIC"] = _default_clients["ANDROID_CREATOR"]
# if you use your own telegram server to surpass 50mb send limit
# apihelper.API_URL = 'http://0.0.0.0:8081/bot{0}/{1}'
# apihelper.FILE_URL = 'http://0.0.0.0:8081'
bot = telebot.TeleBot('') # getting it from https://t.me/BotFather after creating a new bot

def markup_(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    try:
        datasound = (YouTube(message.text).streams.filter(type='audio').order_by('abr').desc().first())
        for i in  (YouTube(message.text).streams.filter(file_extension='mp4').order_by('resolution').desc()):
            # print(i.resolution)
            if i.is_progressive == True :
                res = telebot.types.InlineKeyboardButton(f"{i.resolution} ({i._filesize_mb}MB)", callback_data=f"sound{i.resolution}")
            else:
                res = telebot.types.InlineKeyboardButton(f"{i.resolution} ({i._filesize_mb+(datasound._filesize_mb/2)}MB)", callback_data=f"{i.resolution}")

            markup.add(res)
        bot.send_message(message.chat.id, f"Please select the resolution of {message.text} :", reply_markup=markup)
        return markup
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "Error, Try Again")

def markupx_(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    try:
        for i in (YouTube(message.text).streams.filter(type='audio').order_by('abr').desc()) :
            res = telebot.types.InlineKeyboardButton(f"{i.abr} ({i._filesize_mb}MB)", callback_data=f"music{i.abr}")
            markup.add(res) 
        bot.send_message(message.chat.id, f"Please select the quality of {message.text} :", reply_markup=markup)
        return markup

    except:
        bot.send_message(message.chat.id, "Error, Try Again")


@bot.message_handler(commands=['video', 'music'])
def you(message):
    bot.send_message(message.chat.id, 'Please paste the YouTube video URL:')
    if(message.text[1:] == 'video'):
        bot.register_next_step_handler(message, process_url)
    elif(message.text[1:] == 'music'):
        bot.register_next_step_handler(message, process_urls)


def process_url(message):
    markup_(message)

def process_urls(message):
    markupx_(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_data(call):
    if call.message:
        try:
            if call.data[:5] == 'music':
                download_music(call.message, call.data[5:])
            else :
                download_vid(call.message, call.data)
        except Exception as e :
            print(e)
            try:
                download_vid(call.message, call.data)
            except Exception as e:
                print(e)
                bot.send_message(call.message.chat.id, "Error, Try Again")

def download_vid(message, resolution):
    yt = YouTube(message.text[(message.text).find('http'):(message.text).find(' :')])
    video_title = yt.title
    message_id = bot.send_message(message.chat.id, f"Downloading {video_title} in {resolution} resolution...").message_id
    try:
        if resolution[:5] == 'sound':
            stream = yt.streams.filter(res=resolution[5:],progressive=True).first()
        else :
            stream = yt.streams.filter(res=resolution,progressive=False).first()
    
    except:
        stream = yt.streams.filter(res=resolution).first()



    if stream:
        try:
            if resolution[:5] == 'sound':
                bot.delete_message(message.chat.id, message_id)
                message_id = bot.send_message(message.chat.id, f"Downloading .....").message_id
                title = stream.title
                title = remove_non_english(title)
                # short_title = title
                if len(title) > 30 :
                    short_title = title[:25]
                    title = short_title + '.' + stream.subtype
                else:
                    title = title + '.' + stream.subtype
                stream.download(filename=title)
                bot.delete_message(message.chat.id, message_id)
                message_id = bot.send_message(message.chat.id, f"{stream.title} downloaded successfully. uploading...").message_id
                with open(title, 'rb') as video:
                    bot.send_video(message.chat.id, video, caption=f"Download completed: {stream.title} in {resolution}")
                bot.delete_message(message.chat.id, message_id)
                os.remove(title)
            else:
                bot.delete_message(message.chat.id, message_id)
                message_id = bot.send_message(message.chat.id, f"Downloading .....").message_id
                title = stream.title
                title = remove_non_english(title)
                short_title = title
                if len(title) > 30 :
                    short_title = title[:25]
                    title = short_title + '.' + stream.subtype
                else:
                    title = title + '.' + stream.subtype
                stream.download(filename=title)
                yt.streams.filter(only_audio=True, subtype=stream.subtype).order_by('abr').first().download(filename=short_title+' audio.'+stream.subtype)
                
                input_video = ffmpeg.input(title)

                input_audio = ffmpeg.input(short_title+' audio.'+stream.subtype)

                ffmpeg.output(input_video, input_audio, 'ffmpeg/'+title, codec='copy').run(overwrite_output=True)

                bot.delete_message(message.chat.id, message_id)
                message_id = bot.send_message(message.chat.id, f"{stream.title} downloaded successfully. uploading...").message_id
                with open('ffmpeg/'+title, 'rb') as video:
                    bot.send_video(message.chat.id, video, caption=f"Download completed: {stream.title} in {resolution}")
                bot.delete_message(message.chat.id, message_id)
                os.remove(title)
                os.remove('ffmpeg/'+title)
                os.remove(short_title+' audio.'+stream.subtype)
        except Exception as e:
            print("gagal")
            print(e)
    else:
        bot.send_message(message.chat.id, f"No video found in {resolution} resolution.")

def download_music(message, quality):
    yt = YouTube(message.text[(message.text).find('http'):(message.text).find(' :')])
    video_title = yt.title
    message_id = bot.send_message(message.chat.id, f"Downloading {video_title} in {quality} quality...").message_id
    stream = yt.streams.filter(abr=quality).first()
    if stream:
        bot.delete_message(message.chat.id, message_id)
        message_id = bot.send_message(message.chat.id, f"Downloading .....").message_id
        stream.download()
        
        input_video = ffmpeg.input(stream.default_filename)
        tipe_sub = ''
        if stream.subtype == 'webm' :
            tipe_sub ='.opus'
        else :
            tipe_sub ='.aac'
        ffmpeg.output(input_video, 'ffmpeg/'+stream.title+tipe_sub, codec='copy').run(overwrite_output=True)
        bot.delete_message(message.chat.id, message_id)
        message_id = bot.send_message(message.chat.id, f"{video_title} downloaded successfully. uploading...").message_id
        with open('ffmpeg/'+stream.title+tipe_sub, 'rb') as music:
            bot.send_voice(message.chat.id, music, caption=f"Download completed: {video_title} with the quality of {quality}")
        with open('ffmpeg/'+stream.title+tipe_sub, 'rb') as music:
            bot.send_document(message.chat.id, music, caption=f"The File For {video_title} with the quality of {quality}")
        bot.delete_message(message.chat.id, message_id)
        os.remove('ffmpeg/'+stream.title+tipe_sub)
        os.remove(stream.default_filename)
    else:
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(message.chat.id, f"No video found in {quality} quality.")


bot.polling(non_stop=True)
