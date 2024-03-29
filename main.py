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
        component(["Welcome to Data-Dynamics"], 0, 0, border=True),
        cinput(
            LINES - 1,
            0,
            ":",
            {
                "help": "help",
                "q": "break",
                "r": "reset",
                "login": [0, 5, [login, ["args"]], ["username", "password"]],
                "register": [0, 8, [register, ["args"]], ["username", "password"]],
                "show_anime": [0, 10, show_anime, ["no arguments"]],
                "logout": [0, 6, logout, ["no arguments"]],
                "add_watch": [
                    0,
                    9,
                    [add_watch, ["args"]],
                    ["anime_name", "status"],
                    [get_animes(), ["completed", "dropped", "watching", "planning"]],
                ],
                "search_staff": [
                    0,
                    12,
                    [search_staff, ["args"]],
                    ["anime_name"],
                    [get_animes()],
                ],
                "search_char": [
                    0,
                    11,
                    [search_char, ["args"]],
                    ["anime_name"],
                    [get_animes()],
                ],
                "add_anime": [
                    0,
                    9,
                    [add_anime, ["args"]],
                    [
                        "id",
                        "title",
                        "url",
                        "ENG_title",
                        "JA_title",
                        "score",
                        "rating",
                        "genres",
                        "rank",
                        "aired",
                        "duration",
                        "episode",
                        "favorites",
                        "licensors",
                        "source",
                        "image_url",
                        "studios",
                    ],
                    [
                        [],
                        get_animes(),
                        ["https://"],
                        get_animes(),
                        get_animes(),
                        [],
                        [],
                        [],
                        [],
                        [],
                        [],
                        [],
                        [],
                        [],
                        [],
                        ["https://"],
                        get_studios(),
                    ],
                ],
                "del": [
                    0,
                    3,
                    [delete, ["args"]],
                    [
                        "table",
                        {
                            "anime": "id",
                            "name": "id",
                            "characters": "id",
                            "staff": "name",
                            "watchlist": "id",
                        },
                        {"staff": "anime_id", "watchlist": "anime_id"},
                    ],
                    [
                        ["watchlist", "anime", "characters", "staff", "name"],
                    ],
                ],
            },
            help="Type function",
        ),
    ).build()


def delete(*args):
    success = False
    if PRIVILEGE != "A":
        builder(component(["Failed | Not allowed"], 0, 0, border=True)).build()
        return
    if args[0] == "watchlist":
        parser = argparse.ArgumentParser()
        parser.add_argument("id")
        parser.add_argument("anime_id")
        args = parser.parse_args(args[1:])

        server.execute(
            f"DELETE FROM watchlist WHERE `watchlist`.`id` = {args.id} and `watchlist`.`anime_id` = {args.anime_id}",
            info=False,
        )
        success = True
    elif args[0] == "staff":
        parser = argparse.ArgumentParser()
        parser.add_argument("name")
        parser.add_argument("anime_id")
        args = parser.parse_args(args[1:])

        server.execute(
            f"DELETE FROM staff WHERE `staff`.`anime_id` = {args.anime_id} and `staff`.`name` = {args.name}",
            info=False,
        )
        success = True
    elif args[0] == "anime":
        parser = argparse.ArgumentParser()
        parser.add_argument("id")
        args = parser.parse_args(args[1:])

        server.execute(f"DELETE FROM anime WHERE `anime`.`id` = {args.id}", info=False)
        success = True
    elif args[0] == "name":
        parser = argparse.ArgumentParser()
        parser.add_argument("id")
        args = parser.parse_args(args[1:])

        server.execute(f"DELETE FROM name WHERE `name`.`id` = {args.id}", info=False)
        success = True
    elif args[0] == "characters":
        parser = argparse.ArgumentParser()
        parser.add_argument("id")
        args = parser.parse_args(args[1:])

        server.execute(
            f"DELETE FROM characters WHERE `characters`.`id` = {args.id}", info=False
        )
        success = True
    if success:
        builder(component(["Success"], 0, 0, border=True)).build()


def add_anime(*args):
    if PRIVILEGE != "A":
        builder(component(["Failed | Not allowed"], 0, 0, border=True)).build()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("id")
    parser.add_argument("title")
    parser.add_argument("url")
    parser.add_argument("ENG_title")
    parser.add_argument("JA_title")
    parser.add_argument("score")
    parser.add_argument("rating")
    parser.add_argument("genres")
    parser.add_argument("rank")
    parser.add_argument("aired")
    parser.add_argument("duration")
    parser.add_argument("episodes")
    parser.add_argument("favorites")
    parser.add_argument("licensors")
    parser.add_argument("source")
    parser.add_argument("image_url")
    parser.add_argument("studios")

    if int("".join(args)) < 0:
        builder(component(["Failed | Returned"], 0, 0, border=True)).build()
        return

    args = parser.parse_args(args)

    anime_id = args.id
    title = args.title
    url = args.url
    ENG_title = args.ENG_title
    JA_title = args.JA_title
    score = args.score
    rating = args.rating
    genres = args.genres
    rank = args.rank
    aired = args.aired
    duration = args.duration
    episodes = args.episodes
    favorites = args.favorites
    licensors = args.licensors
    source = args.source
    image_url = args.image_url
    studios = args.studios

    server.execute(
        f"INSERT INTO `anime` (`id`, `title`, `url`, `ENG_title`, `JA_title`, `score`, `rating`, `genres`, `rank`, `aired`, `duration`, `episodes`, `favorites`, `licensors`, `source`, `image_url`, `studios`) VALUES ('anime_{id}', '{title}', '{url}', '{ENG_title}', '{JA_title}', '{score}', '{rating}', '{genres}', '{rank}', '{aired}', '{duration}', '{episodes}', '{favorites}', '{licensors}', '{source}', '{image_url}', '{studios}')"
    )


def get_animes() -> list[list[str, str]]:
    return [
        [i[0], i[1]]
        for i in server.execute("SELECT title, ENG_title FROM anime", info=False)
    ]


def get_studios() -> list[list[str, str]]:
    return [i[0] for i in server.execute("SELECT studios FROM anime", info=False)]


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

    if int("".join(args)) < 0:
        builder(component(["Failed | Returned"], 0, 0, border=True)).build()
        return

    args = parser.parse_args(["".join(args)])
    anime = int(args.anime)
    try:
        anime = str(_return[anime])
    except IndexError:
        builder(component(["Failed | IndexError"], 0, 0, border=True)).build()
        return

    anime_id = get_id(anime)

    characters = server.execute(
        f"SELECT c.name, c.role, c.voice_actor FROM characters AS c JOIN anime AS a ON a.id=c.anime_id WHERE a.id='{anime_id}'",
        info=False,
    )

    _characters = []
    for i in characters:
        __staff = "".join(f" {j} |" for j in i)
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
    res = [f"{times} - {i}" for times, i in enumerate(_return)]
    if len(res) == 1:
        _search_char("0")
    else:
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

    if int("".join(args)) < 0:
        builder(component(["Failed | Returned"], 0, 0, border=True)).build()
        return

    args = parser.parse_args(["".join(args)])
    anime = int(args.anime)
    try:
        anime = str(_return[anime])
    except IndexError:
        builder(component(["Failed | IndexError"], 0, 0, border=True)).build()
        return

    anime_id = get_id(anime)

    staff = server.execute(
        f"SELECT s.name, s.role FROM staff AS s JOIN anime AS a ON a.id=s.anime_id WHERE a.id='{anime_id}'",
        info=False,
    )

    _staff = []
    for i in staff:
        __staff = "".join(f" {j} |" for j in i)
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
    res = [f"{times} - {i}" for times, i in enumerate(_return)]
    if len(res) == 1:
        _search_staff("0")
    else:
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
    global user_id
    global PRIVILEGE
    if ACCOUNT_NAME is None:
        builder(component(["You are not logged in"], 0, 0, border=True)).build()
        return
    ACCOUNT_NAME = None
    user_id = None
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
        success_login(content, username)


# TODO Rename this here and in `login`
def success_login(content, username):
    assert isinstance(content[0][0], int), "Account id should be an integer"
    assert (
        isinstance(content[0][1], str) and content[0][1] in PRIVILEGES
    ), "Invalid privilege"
    ACCOUNT_NAME = username
    ACCOUNT_ID = content[0][0]
    PRIVILEGE = content[0][1]
    if PRIVILEGE == "A":
        priv = "Administrator"
    elif PRIVILEGE == "U":
        priv = "User"
    builder(component([f"{username} Connected as {priv}"], 0, 0, border=True)).build()


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
        max(i[0] for i in server.execute("SELECT id FROM name", info=False)) + 1
    )

    assert server.execute(
        f"SELECT * FROM name WHERE id='{ACCOUNT_ID}'", info=False
    ) in [[], None], "Server error"

    ACCOUNT_NAME = username

    server.execute(
        f"INSERT INTO `name` (`id`, `username`, `joined`, `passw`) VALUES ('{ACCOUNT_ID}', '{username}', '{date}', '{hashlib.sha3_256(bytes(password, encoding='utf-8')).hexdigest()}') ",
        info=False,
    )
    builder(component([f"Success | {username} created"], 0, 0, border=True)).build()


def add_watch(*args) -> None:
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

    if anime_status not in ["completed", "dropped", "watching", "planning"]:
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
    res = [f"{times} - {i}" for times, i in enumerate(_return)]
    if len(res) == 1:
        add_watch_to_dat("0")
    else:
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
                {"": [0, 0, [add_watch_to_dat, ["args"]]]},
                limit=1,
                nof=True,
            ),
        ).build()


def add_watch_to_dat(*args) -> None:
    global _return
    global ACCOUNT_ID
    global anime_status
    parser = argparse.ArgumentParser()
    parser.add_argument("anime")

    if int("".join(args)) < 0:
        builder(component(["Failed | Returned"], 0, 0, border=True)).build()
        return

    args = parser.parse_args(["".join(args)])
    anime = int(args.anime)
    try:
        anime = str(_return[anime])
    except IndexError:
        builder(component(["Failed | IndexError"], 0, 0, border=True)).build()
        return

    id = get_id(anime)

    available = not is_available(id)

    if not available:
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

    if not results:
        return None
    return [query] if query in results else results


def is_available(id) -> bool:
    global ACCOUNT_ID
    _returned = server.execute(
        f"SELECT * FROM watchlist WHERE id='{ACCOUNT_ID}' AND anime_id='{id}'",
        info=False,
    )
    return True if _returned is None else any(len(i) == 0 for i in _returned)


wrapper(main)


# DELETE FROM watchlist WHERE id='ACCOUNT_ID' AND anime_id='id'
