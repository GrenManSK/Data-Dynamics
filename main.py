"""_summary_
Richard Melniček
Samuel Pribulla
Juraj Durkáč

Data-Dynamics

13.06.2023
"""

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

PRIVILEGES = ["U", "A"]

ACCOUNT_NAME = None
ACCOUNT_ID = None
PRIVILEGE = None

date = datetime.now().strftime("%Y-%m-%d")

_return = None
anime_status = None


def main(stdscr) -> None:
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
                "login": [0, 5, [login, ["args"]], ["username", "password"]],
                "register": [0, 8, [register, ["args"]], ["username", "password"]],
                "show_anime": [0, 10, show_anime, ["no arguments"]],
                "logout": [0, 6, logout, ["no arguments"]],
                "add_anime": [0, 9, [add_anime, ["args"]], ["anime_name", "status"]],
                "search_staff": [0, 12, [search_staff, ["args"]], ["anime_name"]],
                "search_char": [0, 11, [search_char, ["args"]], ["anime_name"]],
            },
        )
    ).build()


def get_animes() -> list[list[str, str]]:
    return [
        [i[0], i[1]]
        for i in server.execute("SELECT title, ENG_title FROM anime", info=False)
    ]


def get_id(anime) -> str:
    return str(
        [
            i[0]
            for i in server.execute(
                f"SELECT id FROM anime WHERE title='{anime}' OR ENG_title='{anime}'",
                info=False,
            )
        ][0]
    )


def _search_char(*args):
    global _return
    parser = argparse.ArgumentParser()
    parser.add_argument("anime")

    args = parser.parse_args(["".join(args)])
    anime = int(args.anime)
    anime = str(_return[anime])

    id = get_id(anime)

    characters = server.execute(
        f"SELECT c.name, c.role, c.voice_actor FROM characters AS c JOIN anime AS a ON a.id=c.anime_id WHERE a.id='{id}'",
        info=False,
    )

    _characters = []
    for i in characters:
        __staff = ""
        for j in i:
            __staff += f" {j} |"
        _characters.append(__staff[:-1])

    builder(component([*_characters], 0, 0, border=True)).build()


def search_char(*args):
    global _return
    if ACCOUNT_NAME is None:
        builder(component(["You are not logged in"], 0, 0, border=True)).build()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("anime")
    args = parser.parse_args(args)
    anime = args.anime.replace("_", " ")

    animes = get_animes()
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
            {"": [0, 0, [_search_char, ["args"]]]},
            limit=1,
            nof=True,
        ),
    ).build()


def _search_staff(*args):
    global _return
    parser = argparse.ArgumentParser()
    parser.add_argument("anime")

    args = parser.parse_args(["".join(args)])
    anime = int(args.anime)
    anime = str(_return[anime])

    id = get_id(anime)

    staff = server.execute(
        f"SELECT s.name, s.role FROM staff AS s JOIN anime AS a ON a.id=s.anime_id WHERE a.id='{id}'",
        info=False,
    )

    _staff = []
    for i in staff:
        __staff = ""
        for j in i:
            __staff += f" {j} |"
        _staff.append(__staff[:-1])

    builder(component([*_staff], 0, 0, border=True)).build()


def search_staff(*args):
    global _return
    if ACCOUNT_NAME is None:
        builder(component(["You are not logged in"], 0, 0, border=True)).build()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("anime")
    args = parser.parse_args(args)
    anime = args.anime.replace("_", " ")

    animes = get_animes()
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
            {"": [0, 0, [_search_staff, ["args"]]]},
            limit=1,
            nof=True,
        ),
    ).build()


def show_anime() -> None:
    if ACCOUNT_NAME is None:
        builder(component(["You are not logged in"], 0, 0, border=True)).build()
        return
    content = server.execute(
        f"SELECT a.title, w.status FROM anime AS a JOIN watchlist AS w ON a.id=w.anime_id JOIN name AS n ON w.id=n.id WHERE n.username='{ACCOUNT_NAME}'",
        info=False,
    )
    content = [f"{i[0]} | {i[1]}" for i in content]
    builder(component(content, 0, 0, border=True)).build()


def logout() -> None:
    global ACCOUNT_NAME
    global id
    global PRIVILEGE
    if ACCOUNT_NAME is None:
        builder(component(["You are not logged in"], 0, 0, border=True)).build()
        return
    ACCOUNT_NAME = None
    id = None
    PRIVILEGE = None
    builder(component(["You are logged out"], 0, 0, border=True)).build()


def login(*args) -> None:
    global ACCOUNT_ID
    global ACCOUNT_NAME
    global PRIVILEGE
    if ACCOUNT_NAME is not None:
        builder(component(["Failed | Already logged in"], 0, 0, border=True)).build()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    args = parser.parse_args(args)
    username = args.username.replace("_", " ")
    password = args.password
    content = server.execute(
        f"SELECT n.id, n.privilege FROM name AS n WHERE n.username='{username}' AND n.passw='{hashlib.sha3_256(bytes(password, encoding='utf-8')).hexdigest()}'",
        info=False,
    )

    if len(content) == 0:
        builder(
            component(["Failed | Wrong username or password"], 0, 0, border=True)
        ).build()
    if len(content) == 1:
        assert isinstance(content[0][0], int), "Account id should be an integer"
        assert (
            isinstance(content[0][1], str) and content[0][1] in PRIVILEGES
        ), "Invalid privilege"
        ACCOUNT_NAME = username
        ACCOUNT_ID = content[0][0]
        PRIVILEGE = content[0][1]
        if PRIVILEGE == "U":
            priv = "User"
        elif PRIVILEGE == "A":
            priv = "Administrator"
        builder(
            component([username + " Connected as " + priv], 0, 0, border=True)
        ).build()


def register(*args) -> None:
    global ACCOUNT_NAME
    global ACCOUNT_ID
    if ACCOUNT_NAME is not None:
        builder(component(["Failed | Already logged in"], 0, 0, border=True)).build()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    args = parser.parse_args(args)
    username = args.username.replace("_", " ")
    password = args.password

    assert len(username) > 0, "Username must not be empty"
    assert len(password) > 0, "Password must not be empty"

    ACCOUNT_ID = (
        max([i[0] for i in server.execute("SELECT id FROM name", info=False)]) + 1
    )

    assert server.execute(
        f"SELECT * FROM name WHERE id='{ACCOUNT_ID}'", info=False
    ) in [[], None], "Server error"

    ACCOUNT_NAME = username

    server.execute(
        f"INSERT INTO `name` (`id`, `username`, `joined`, `passw`) VALUES ('{ACCOUNT_ID}', '{username}', '{date}', '{hashlib.sha3_256(bytes(password, encoding='utf-8')).hexdigest()}') ",
        info=False,
    )
    builder(component([f"Sucess | {username} created"], 0, 0, border=True)).build()


def add_anime(*args) -> None:
    global LINES
    global _return
    global anime_status
    if ACCOUNT_NAME is None:
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

    animes = get_animes()
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


def add_anime_to_dat(*args) -> None:
    global _return
    global ACCOUNT_ID
    global anime_status
    parser = argparse.ArgumentParser()
    parser.add_argument("anime")

    args = parser.parse_args(args)
    anime = int(args.anime)
    anime = str(_return[anime])

    id = get_id(anime)

    available = not is_available(id)

    if available:
        server.execute(
            f"INSERT INTO `watchlist` (`id`, `anime_id`, `status`) VALUES ('{ACCOUNT_ID}', '{id}', '{anime_status}') ",
            info=False,
        )
    elif not available:
        server.execute(
            f"DELETE FROM watchlist WHERE id='{ACCOUNT_ID}' AND anime_id='{id}'",
            info=False,
        )
        server.execute(
            f"INSERT INTO `watchlist` (`id`, `anime_id`, `status`) VALUES ('{ACCOUNT_ID}', '{id}', '{anime_status}') ",
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


def search_engine(query, data) -> None | list[str]:
    query_words = query.lower().split()

    results = []
    for item in data:
        for text in item:
            words = text.lower().replace('"', "").replace("'", "").split()
            match = True
            for query_word in query_words:
                word_matched = False
                for word in words:
                    distance = Levenshtein.distance(query_word, word)
                    if distance <= 1:
                        word_matched = True
                        break
                if not word_matched:
                    match = False
                    break
            if match:
                results.append(text)
                break

    if results:
        return results
    else:
        return None


def is_available(id) -> bool:
    global ACCOUNT_ID
    _returned = server.execute(
        f"SELECT * FROM wachlist WHERE id='{ACCOUNT_ID}' AND anime_id='{id}'",
        info=False,
    )
    if _returned is None:
        return True
    for i in _returned:
        if len(i) == 0:
            return True
    return False


wrapper(main)


# DELETE FROM watchlist WHERE id='ACCOUNT_ID' AND anime_id='id'
