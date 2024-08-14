import os
import json
import random
import requests

from base64 import b64encode
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template

load_dotenv(find_dotenv())

# Spotify scopes:
#   user-read-currently-playing
#   user-read-recently-played
PLACEHOLDER_IMAGE = os.getenv("PLACEHOLDER_IMAGE")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_SECRET_ID = os.getenv("SPOTIFY_SECRET_ID")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")

FALLBACK_THEME = "spotify.html.j2"

REFRESH_TOKEN_URL = os.getenv("REFRESH_TOKEN_URL")
NOW_PLAYING_URL = os.getenv("NOW_PLAYING_URL")
RECENTLY_PLAYING_URL = os.getenv("RECENTLY_PLAYING_URL")

app = Flask(__name__)


def get_auth():
    return b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_SECRET_ID}".encode()).decode(
        "ascii"
    )


def refresh_token():
    data = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN,
    }

    headers = {"Authorization": "Basic {}".format(get_auth())}
    response = requests.post(REFRESH_TOKEN_URL, data=data, headers=headers)

    try:
        return response.json()["access_token"]
    except KeyError:
        print(json.dumps(response.json()))
        print("\n---\n")
        raise KeyError(str(response.json()))


def recently_played():
    token = refresh_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(RECENTLY_PLAYING_URL, headers=headers)

    if response.status_code == 204:
        return {}
    return response.json()


def now_playing():
    token = refresh_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(NOW_PLAYING_URL, headers=headers)

    if response.status_code == 204:
        return {}
    return response.json()


def bar_gen(bar_count):
    bar_css = ""
    left = 1
    for i in range(1, bar_count + 1):
        anim = random.randint(1000, 1350)
        bar_css += (
            ".bar:nth-child({})  {{ left: {}px; animation-duration: {}ms; }}".format(
                i, left, anim
            )
        )
        left += 4
    return bar_css


def get_template():
    try:
        file = open("templates.json", "r")
        templates = json.loads(file.read())
        return templates["templates"][templates["current-theme"]]
    except Exception as e:
        print(f"Failed to load templates.")
        return FALLBACK_THEME


def load_image_b64(url):
    response = requests.get(url)
    return b64encode(response.content).decode("ascii")


def make_svg(data, background_color, border_color):
    bar_count = 84
    content_bar = "".join(["<div class='bar'></div>" for i in range(bar_count)])
    bar_css = bar_gen(bar_count)

    if data == {} or data["item"] == "None" or data["item"] is None:
        # contentBar = "" #Shows/Hides the EQ bar if no song is currently playing
        current_status = "Was playing:"
        recent_plays = recently_played()
        recent_plays_length = len(recent_plays["items"])
        item_index = random.randint(0, recent_plays_length - 1)
        item = recent_plays["items"][item_index]["track"]
    else:
        item = data["item"]
        current_status = "Vibing to:"

    if item["album"]["images"] == []:
        image = PLACEHOLDER_IMAGE
    else:
        image = load_image_b64(item["album"]["images"][1]["url"])

    artist_name = item["artists"][0]["name"].replace("&", "&amp;")
    song_name = item["name"].replace("&", "&amp;")
    song_uri = item["external_urls"]["spotify"]
    artist_uri = item["artists"][0]["external_urls"]["spotify"]

    data_dict = {
        "content_bar": content_bar,
        "bar_css": bar_css,
        "artist_name": artist_name,
        "song_name": song_name,
        "song_uri": song_uri,
        "artist_uri": artist_uri,
        "image": image,
        "status": current_status,
        "background_color": background_color,
        "border_color": border_color
    }

    with app.app_context():
        return render_template(get_template(), **data_dict)


def catch_all():
    background_color = "181414"
    border_color = "181414"

    data = now_playing()
    svg = make_svg(data, background_color, border_color)
    path = 'assets/banners/spotify.svg'

    with open(path, 'w') as f:
        f.write(svg)


if __name__ == "__main__":
    catch_all()
