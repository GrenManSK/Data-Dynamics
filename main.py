import curses
from curses import wrapper
from curses_builder import builder, component, cinput, init, history, history_number
import argparse
from final.sql import SQLServer
import hashlib
from dotenv import load_dotenv
import os

load_dotenv(".env")


HOST_NAME = "localhost"
PORT = 3306
USER = "root"
PASSWORD = os.getenv('PASSWORD')
DATABASE = os.getenv('DATABASE')

server = SQLServer(
    HOST_NAME, port=PORT, user=USER, passwd=PASSWORD, database=DATABASE, log=True
)

server.connect()

account_name = None


def main(stdscr):
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
                "register": [0, 8, [register, ["args"]]],
                "show_anime": [0, 10, show_anime],
                "logout": [0, 6, logout],
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
        f"SELECT a.title, w.status FROM anime AS a JOIN watchlist AS w ON a.id=w.anime_id JOIN name AS n ON w.id=n.id WHERE n.username='{username}'"
    )
    content = [f"{i[0]} | {i[1]}" for i in content]
    builder(component(content, 0, 0, border=True)).build()


def logout():
    global account_name
    if account_name is None:
        builder(component(["You are not logged in"], 0, 0, border=True)).build()
        return
    account_name = None
    builder(component(["You are logged out"], 0, 0, border=True)).build()


def register(*args):
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
        f"SELECT n.username, n.passw FROM name AS n WHERE n.username='{username}' AND n.passw='{hashlib.sha3_256(bytes(password, encoding='utf-8')).hexdigest()}'"
    )
    if len(content) == 0:
        builder(
            component(["Failed | Wrong username or password"], 0, 0, border=True)
        ).build()
    if len(content) == 1:
        account_name = username
        builder(component([username + " Connected"], 0, 0, border=True)).build()


wrapper(main)
