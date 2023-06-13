import curses
from curses import wrapper
from curses_builder import builder, component, cinput, init
import argparse
from final.sql import SQLServer
import hashlib
from dotenv import load_dotenv
import os
from datetime import datetime
import Levenshtein

load_dotenv(".env")

COLS = None
LINES = None


HOST_NAME = os.getenv("HOST_NAME")
PORT = os.getenv("DAT_PORT")
USER = os.getenv("DAT_USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")

server = SQLServer(
    HOST_NAME, port=PORT, user=USER, passwd=PASSWORD, database=DATABASE, log=False
)

server.connect()

account_name = None
account_id = None
date = datetime.now().strftime("%Y-%m-%d")

_return = None
anime_status = None


def main(stdscr):
    global COLS
    global LINES
    COLS = curses.COLS
    LINES = curses.LINES
    init(stdscr)
    builder(
        cinput(
            LINES - 1,
            0,
            ":",
            {
                "q": "break",
                "r": "reset",
                "login": [0, 5, [login, ["args"]]],
                "register": [0, 8, [register, ["args"]]],
                "show_anime": [0, 10, show_anime],
                "logout": [0, 6, logout],
                "add_anime": [0, 9, [add_anime, ["args"]]],
            },
        )
    ).build()
    pass


def show_anime():
    if account_name is None:
        builder(component(["You are not logged in"], 0, 0, border=True)).build()
        return
    username = account_name
    content = server.execute(
        f"SELECT a.title, w.status FROM anime AS a JOIN watchlist AS w ON a.id=w.anime_id JOIN name AS n ON w.id=n.id WHERE n.username='{username}'",
        info=False,
    )
    content = [f"{i[0]} | {i[1]}" for i in content]
    builder(component(content, 0, 0, border=True)).build()


def logout():
    global account_name
    global id
    if account_name is None:
        builder(component(["You are not logged in"], 0, 0, border=True)).build()
        return
    account_name = None
    id = None
    builder(component(["You are logged out"], 0, 0, border=True)).build()


def login(*args):
    global account_id
    global account_name
    if account_name is not None:
        builder(component(["Failed | Already logged in"], 0, 0, border=True)).build()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    args = parser.parse_args(args)
    username = args.username.replace("_", " ")
    password = args.password
    content = server.execute(
        f"SELECT n.username, n.passw, n.id FROM name AS n WHERE n.username='{username}' AND n.passw='{hashlib.sha3_256(bytes(password, encoding='utf-8')).hexdigest()}'",
        info=False,
    )
    if len(content) == 0:
        builder(
            component(["Failed | Wrong username or password"], 0, 0, border=True)
        ).build()
    if len(content) == 1:
        account_name = username
        account_id = content[0][2]
        builder(component([username + " Connected"], 0, 0, border=True)).build()


def register(*args):
    global account_name
    global account_id
    if account_name is not None:
        builder(component(["Failed | Already logged in"], 0, 0, border=True)).build()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    args = parser.parse_args(args)
    username = args.username.replace("_", " ")
    password = args.password
    account_id = (
        max([i[0] for i in server.execute("SELECT id FROM name", info=False)]) + 1
    )
    account_name = username

    server.execute(
        f"INSERT INTO `name` (`id`, `username`, `joined`, `passw`) VALUES ('{account_id}', '{username}', '{date}', '{hashlib.sha3_256(bytes(password, encoding='utf-8')).hexdigest()}') ",
        info=False,
    )
    builder(component([f"Sucess | {username} created"], 0, 0, border=True)).build()


def add_anime(*args):
    global LINES
    global _return
    global anime_status
    if account_name is None:
        builder(component(["You are not logged in"], 0, 0, border=True)).build()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("anime")
    parser.add_argument("status")

    args = parser.parse_args(args)
    anime = args.anime.replace("_", " ")
    anime_status = args.status

    if not anime_status in ["completed", "dropped", "watching", "planning"]:
        builder(
            component(
                [
                    f"Status is not supported | Available: {['completed', 'dropped', 'watching', 'planning']}"
                ],
                0,
                0,
                border=True,
            )
        ).build()
        return

    animes = [
        [i[0], i[1]]
        for i in server.execute("SELECT title, ENG_title FROM anime", info=False)
    ]
    _return = search_engine(anime, animes)
    res = []
    for times, i in enumerate(_return):
        res.append(f"{times} - {i}")

    builder(
        component(
            [*res],
            0,
            0,
            border=True,
        ),
        cinput(
            LINES - 1,
            0,
            "",
            {"": [0, 0, [add_anime_to_dat, ["args"]]]},
            limit=1,
            nof=True,
        ),
    ).build()


def add_anime_to_dat(*args):
    global _return
    global account_id
    global anime_status
    parser = argparse.ArgumentParser()
    parser.add_argument("anime")

    args = parser.parse_args(args)
    anime = int(args.anime)
    anime = str(_return[anime])

    id = str(
        [
            i[0]
            for i in server.execute(
                f"SELECT id FROM anime WHERE title='{anime}' OR ENG_title='{anime}'",
                info=False,
            )
        ][0]
    )

    available = is_available(id)

    if not available:
        server.execute(
            f"INSERT INTO `watchlist` (`id`, `anime_id`, `status`) VALUES ('{account_id}', '{id}', '{anime_status}') ",
            info=False,
        )
    if available:
        server.execute(
            f"DELETE FROM watchlist WHERE id='{account_id}' AND anime_id='{id}'",
            info=False,
        )
        server.execute(
            f"INSERT INTO `watchlist` (`id`, `anime_id`, `status`) VALUES ('{account_id}', '{id}', '{anime_status}') ",
            info=False,
        )

    builder(
        component(
            [anime, id],
            0,
            0,
            border=True,
        ),
    ).build()

    anime_status = None
    _return = None


def search_engine(query, data):
    query_words = query.lower().split()

    results = []
    for item in data:
        for text in item:
            words = text.lower().replace('"', "").replace("'", "").split()
            match = True
            for query_word in query_words:
                for word in words:
                    distance = Levenshtein.distance(query_word.lower(), word.lower())
                    if distance <= 1:
                        match = True
                        break
                    else:
                        match = False
                        pass
                if match:
                    break

            if match:
                results.append(text)
                break

    if results:
        return results
    else:
        print("No results found for '{}'".format(query))


def is_available(id):
    global account_id
    _returned = server.execute(
        f"SELECT * FROM wachlist WHERE id='{account_id}' AND anime_id='{id}'",
        info=False,
    )
    if _returned is None:
        return True
    for i in _returned:
        if len(i) == 0:
            return True
    return False


wrapper(main)


# DELETE FROM watchlist WHERE id='account_id' AND anime_id='id'
