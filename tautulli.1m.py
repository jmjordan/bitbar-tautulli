#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# <bitbar.title>Tautulli Activity</bitbar.title>
# <bitbar.version>v0.9</bitbar.version>
# <bitbar.author>Jonathan Jordan</bitbar.author>
# <bitbar.author.github>jmjordan</bitbar.author.github>
# <bitbar.desc>Show Plex activity using Tautulli API</bitbar.desc>
# <bitbar.dependencies>plex,tautulli,pyplex,python</bitbar.dependencies>
import json
import os
import urllib.request
import base64
from datetime import datetime, timedelta

PLUGIN_PATH = os.path.join(os.getcwd(), __file__)

# ---
# Variables
# ---

# URL the Tautulli
tautulli_base_url = "http://{TAUTULLI_HOST}:8181"
apikey = "{TAUTULLI_API_KEY}"
plex_url = "{PLEX_URL}"

# API urls
url_activity = f'{tautulli_base_url}/api/v2?apikey={apikey}&cmd=get_activity'
url_history = f'{tautulli_base_url}/api/v2?apikey={apikey}&cmd=get_history&length=5&include_activity=0'
SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

# ---
# Helper methods
# ---

def do_request(url, method='GET'):
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req)
    return json.loads(response.read())


def get_activity():
    response = do_request(url_activity)
    return response

def get_history():
    response = do_request(url_history)
    return response

def separator():
    print('---')

# Data
activity = get_activity()
history = get_history()

decision = {'direct play': 'Direct Play', 'copy': 'Direct Stream', 'transcode': 'Transcode'}
media_type = {'episode': '􀎲', 'movie': '􀎶', 'track': '􀑪'}

def session_quality(session):
    quality = session['quality_profile']
    media_type = session['media_type']
    if quality == 'Original':
        if media_type != 'track':
            video_resolution = session['stream_video_full_resolution']
            stream_dynamic_range = session['stream_video_dynamic_range']
            if stream_dynamic_range == 'HDR':
                video_resolution += ' HDR'
            video_bitrate = int(session['stream_bitrate'])/1000
            return f'{video_resolution} / {video_bitrate:.1f} Mbps'
        else:
            audio_bitrate = session['bitrate']
            return f'{audio_bitrate} kbps'
    else:
        return f'{quality}'

def session_summary(session):
    thumb = session['parent_thumb'] or session['grandparent_thumb'] if session['media_type'] == 'episode' else session['thumb']
    img = None
    if thumb:
        req = urllib.request.Request(f'{tautulli_base_url}/api/v2?apikey={apikey}&cmd=pms_image_proxy&img={thumb}&height=75')
        try:
            response = urllib.request.urlopen(req)
            data = response.read()
            img = base64.b64encode(data).decode('utf-8')
        except:
            pass
    state = '􀊄' if session['state'] == 'playing' else '􀊆'
    user = session['username']
    full_title = session['full_title']
    if session['media_type'] == 'episode':
        show = session['grandparent_title']
        season = session['parent_media_index']
        episode = session['media_index']
        name = session['title']
        full_title = f'{show} - S{season} • E{episode}\\n{name}'
    elif session['media_type'] == 'movie':
        title = full_title
        year = session['year']
        full_title = f'{title}\\n{year}'
    elif session['media_type'] == 'track':
        track = session['media_index']
        title = session['title']
        artist = session['grandparent_title']
        album = session['parent_title']
        full_title = f'{track} - {title}\\n{artist} — {album}'

    rating_key = session['rating_key']
    if img:
        return f'{user}\\n{state}  {full_title} | image={img} href={tautulli_base_url}/info?rating_key={rating_key}'
    else:
        return f'{user}\\n{state}  {full_title} | href={tautulli_base_url}/info?rating_key={rating_key}'

def session_time(session):
    total_duration = int(session['duration'])/1000
    progress = int(session['progress_percent'])/100
    watched_duration = progress * total_duration
    
    duration_delta = str(timedelta(seconds=int(total_duration))).lstrip('0').lstrip(':')
    watched_delta = str(timedelta(seconds=int(watched_duration))).lstrip('0').lstrip(':')

    return f'{watched_delta} / {duration_delta} | sfimage=clock'

def session_video(session):
    video_decision = session['stream_video_decision']

    video_codec = session['video_codec'].upper()
    video_resolution = session['video_full_resolution']

    stream_codec = session['stream_video_codec'].upper()
    stream_resolution = session['stream_video_full_resolution']
    if video_decision == 'transcode':

        if session['transcode_hw_decoding']:
            video_codec = '􀫥' + video_codec
       
        if session['transcode_hw_encoding']:
            stream_codec = '􀫥' + stream_codec

        decoding = f'{video_codec} {video_resolution}'
        encoding = f'{stream_codec} {stream_resolution}'

        return f'{decision[video_decision]} • {decoding} → {encoding} | sfimage=v.square.fill'
    else:
        return f'{decision[video_decision]} • {stream_codec} {stream_resolution} | sfimage=v.square.fill'

def session_audio(session):
    audio_decision = session['stream_audio_decision']
    audio_codec = session['audio_codec'].upper()
    audio_channels = session['audio_channel_layout'].split('(')[0]

    stream_audio_codec = session['stream_audio_codec'].upper()
    stream_audio_channels = session['stream_audio_channel_layout'].split('(')[0]
    if audio_decision == 'transcode':
        decoding = f'{audio_codec} {audio_channels}'
        encoding = f'{stream_audio_codec} {stream_audio_channels}'
        return f'{decision[audio_decision]} • {decoding} → {encoding} | sfimage=a.square.fill'
    else:
        return f'{decision[audio_decision]} • {stream_audio_codec} | sfimage=a.square.fill'

def session_location(session):
    location = session['location'].upper()
    ip_address = session['ip_address']
    secure = 'lock.fill' if session['secure'] else 'lock.open.fill'
    if session['location'] == 'wan':
        url = f'{tautulli_base_url}/api/v2?apikey={apikey}&cmd=get_geoip_lookup&ip_address={ip_address}'
        geo_response = do_request(url)
        city = geo_response['response']['data']['city']
        state = geo_response['response']['data']['region']
        return f'{location}: {ip_address} • {city}, {state} | sfimage={secure}'
    else:
        return f'{location}: {ip_address} | sfimage={secure}'


def title(count):
    count_str = str(count).translate(SUBSCRIPTS) if count > 0 else ''
    title_str = f' ❯ {count_str}| size=18 baselineOffset=-1'
    if count > 0:
        title_str += ' color=#cc7b19'
    return title_str
    
def history_summary(session):
    user = session['user']
    media = media_type[session['media_type']]
    title = session['full_title']

    if session['media_type'] == 'episode':
        show = session['grandparent_title']
        season = session['parent_media_index']
        episode = session['media_index']
        name = session['title']
        title = f'{show} - S{season} • E{episode}'
    ended = datetime.fromtimestamp(session['stopped']).strftime('%b %d')
    return f'{media} {ended} • {user} • {title}'

# Layout    
def bitbar():
    stream_count = int(activity['response']['data']['stream_count'])
    stream_unit = 'stream' if stream_count == 1 else 'streams'

    # Menubar icon
    print(title(stream_count))
    separator()

    print(f'Open Tautulli | href={tautulli_base_url}/home')
    print(f'Open Plex | href={plex_url}')
    separator()

    if stream_count == 0:
        print('Idle')
    else:
        lan_bandwidth = activity['response']['data']['lan_bandwidth']/1000
        wan_bandwidth = activity['response']['data']['wan_bandwidth']/1000
        print(f'{stream_count} {stream_unit}')
        if lan_bandwidth:
            print(f'LAN: {lan_bandwidth:.1f} Mbps')
        if wan_bandwidth:
            print(f'WAN: {wan_bandwidth:.1f} Mbps')
        for session in activity['response']['data']['sessions']:
            media_type = session['media_type']
            if media_type == 'photo':
                continue

            separator()
            print(session_summary(session))
            print(session_time(session))
            if media_type != 'track':
                print(session_video(session)) 
            print(session_audio(session))
            print(session_location(session))
    
    history_data = history['response']['data']['data']
    if len(history_data):
        separator()
        for h in history_data:
            print(history_summary(h))

# Execution
try:
    bitbar()
except Exception as e:
    print('Script error:')
    print(e)
    separator()
