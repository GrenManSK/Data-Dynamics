import curses
import copy
from random import randint

VERSION = "1.0.1"
AUTHOR = "GrenManSK"


def get_id(long: int = 10) -> int:
    id = ""
    for i in range(long):
        id += str(randint(0, 9))
    return id


window = {}
current_row = 0

global in_func
history = {}
history_number = 0
in_func = False
func_reset = False
last_command_history = {}
ids = {}
current_id = None


class OnlyOneCharKey(Exception):
    pass


def init(stdscr_temp):
    global stdscr
    global COLS
    global LINES
    stdscr = stdscr_temp
    COLS = curses.COLS
    LINES = curses.LINES


def string(
    y: int,
    x: int,
    content: str,
    move: int = 0,
    refresh: bool = True,
    register: bool = True,
) -> None:
    global window
    global current_row
    if y == "type":
        return
    try:
        stdscr.addstr(y, x, content)
    except curses.error:
        pass
    if register:
        try:
            if window[y] is not None:
                if len(window[y]) < x:
                    window[y] = window[y] + (x - len(window[y])) * " " + content
                else:
                    window[y] = window[y][0:x] + content + window[y][x + len(content) :]
        except KeyError:
            window[y] = " " * x + content
    current_row += move
    if refresh:
        stdscr.refresh()


class builder:
    def __init__(self, *args):
        self.lenght = len(args)
        cin = 0
        comp = 0
        for times, arg in enumerate(args):
            if isinstance(arg, cinput):
                setattr(self, f"zcinput_{cin}", arg())
                cin += 1
            if isinstance(arg, component):
                setattr(self, f"component_{comp}", arg())
                comp += 1

    def add_history(self, window_temp):
        global history_number
        global func_reset
        try:
            if history[history_number] == history[history_number - 1]:
                return
        except KeyError:
            pass
        if not in_func and not func_reset:
            history[history_number] = copy.deepcopy(window_temp)
            history_number += 1
            window = copy.deepcopy(window_temp)

    def reset(self, window_temp):
        global history_number
        global window
        global func_reset
        for i in range(LINES):
            string(i, 0, COLS * " ", register=False)
        for times, content in window_temp.items():
            string(times, 0, content, register=False)
        self.add_history(window_temp)

    def restore(self, command):
        for y in command:
            x = command[y][0]
            content = len(command[y][1].strip()) * " "
            string(
                y,
                x,
                content,
            )

    def build(self):
        global history_number
        global in_func
        global func_reset
        global current_id
        for f in dir(self):
            if str(f).startswith("component_"):
                for times, content in eval(f"self.{f}").items():
                    if times == "type":
                        continue
                    string(times, content[0], content[1])
                    if in_func:
                        last_command_history[ids[current_id]] = {}
                        last_command_history[ids[current_id]][times] = [
                            content[0],
                            content[1],
                        ]
                self.add_history(window)
            elif str(f).startswith("zcinput_"):
                ikey = None
                x = None
                y = None
                border = None
                function = None
                width = None
                for times, content in eval(f"self.{f}").items():
                    if times == "type":
                        continue
                    elif times == "key":
                        if len(content) > 1:
                            raise OnlyOneCharKey(
                                "You must provide a key, not combination"
                            )
                        ikey = content
                        continue
                    elif times == "x":
                        x = content
                        continue
                    elif times == "y":
                        y = content
                        continue
                    elif times == "border":
                        border = content
                        continue
                    elif times == "function":
                        function = content
                        continue
                    elif times == "limit":
                        limit = content
                        continue
                    elif times == "nof":
                        nof = content
                        continue
                    elif times == "width":
                        width = content
                        continue
                    string(times, content[0], content[1])
                if border:
                    string(y, x + 1, "_")
                else:
                    string(y, x, " ")
                inp = False
                vstup = ""
                end = False
                history_in_row = 0
                last_command = None
                self.add_history(window)
                pocet = 0
                _func = None
                is_func = False
                arg_num = 0
                arg_num_hist = -1
                while True:
                    func_reset = False
                    konecna = False
                    if not vstup[1:pocet] in function.keys() and is_func:
                        string(y - 1, x, COLS * " ")
                        string(y, x + len(_func) + 1, "")
                        is_func = False
                    if vstup[1:] in function.keys():
                        _func = vstup[1:]
                        if not _func in ["q", "r"]:
                            is_func = True
                            pocet = len(_func) + 1
                    if is_func:
                        arg_num = len(vstup.split(" ")) - 2
                        if arg_num == -1:
                            arg_num = 0
                        if arg_num != arg_num_hist:
                            if border:
                                string(y - 1, x, COLS * "_")
                            else:
                                string(y - 1, x, COLS * " ")
                            nam = vstup.split(" ")
                            if len(nam) == 1:
                                posun = len(_func) + 2
                            else:
                                posun = sum([len(i) for i in vstup.split(" ")[:-1]]) + 2
                            try:
                                string(y - 1, x + posun, function[_func][3][arg_num])
                                string(y, x + len(vstup), "")
                            except IndexError:
                                pass
                            arg_num_hist = arg_num
                    if ikey == "" and not inp:
                        inp = True
                        vstup += ikey
                        # curses.nocbreak()
                        # stdscr.keypad(False)
                        curses.echo()
                        string(y + 1, x, ikey)
                    key = stdscr.getkey()
                    if inp:
                        if not key == "\n":
                            if key == "\x08":
                                vstup = vstup[0:-1]
                                if vstup == "":
                                    vstup = ":"
                                string(y, x + len(vstup), "")
                            else:
                                vstup += key
                        else:
                            vstup = vstup.strip() + " "
                    if key == ikey:
                        inp = True
                        vstup += ikey
                        # curses.nocbreak()
                        # stdscr.keypad(False)
                        curses.echo()
                        if border:
                            string(y + 1, x, ikey)
                        else:
                            string(y, x, ikey)
                    if key == "\n":
                        konecna = True
                        inp = False
                        curses.cbreak()
                        stdscr.keypad(True)
                        curses.noecho()
                        if border:
                            string(y + 1, x, int(COLS - 1 - x) * "_")
                            string(y - 1, x, COLS * "_")
                        else:
                            string(y, x, int(COLS - 1 - x) * " ")
                            string(y - 1, x, COLS * " ")
                    if konecna:
                        limit -= 1
                        if not ikey == "":
                            vstup = vstup[1:-1]
                        else:
                            vstup = vstup[:-1]
                        for func in function:
                            to_func = False
                            func_args = None
                            if isinstance(function[func], list):
                                if len(function[func]) == 2:
                                    func_args = function[func][1]
                                    if not isinstance(func_args, list):
                                        raise ValueError()
                                    if func == vstup.split(" ")[0]:
                                        if function[func][1][0] == "args":
                                            func_args = vstup[len(func) :].split(" ")
                                            func_args = list(
                                                filter(("").__ne__, func_args)
                                            )
                                        command = function[func][0]
                                        to_func = True
                                        try:
                                            ids[func]
                                        except KeyError:
                                            ids[func] = get_id()
                                elif (
                                    func == vstup[function[func][0] : function[func][1]]
                                ):
                                    to_func = True
                                    if callable(function[func][2]):
                                        command = function[func][2]
                                    elif len(function[func][2]) == 2:
                                        if function[func][2][1][0] == "args":
                                            try:
                                                func_args = vstup.split(" ", 1)[
                                                    1
                                                ].split(" ")
                                            except IndexError:
                                                if nof:
                                                    func_args = vstup
                                                else:
                                                    raise ValueError
                                            func_args = list(
                                                filter(("").__ne__, func_args)
                                            )
                                        else:
                                            func_args = function[func][2][1]
                                            if not isinstance(func_args, list):
                                                raise ValueError()
                                        command = function[func][2][0]
                                    else:
                                        command = function[func][2]
                                    try:
                                        ids[func]
                                    except KeyError:
                                        ids[func] = get_id()
                            else:
                                if func == vstup:
                                    try:
                                        ids[func]
                                    except KeyError:
                                        ids[func] = get_id()
                                    to_func = True
                                    command = function[func]

                            if to_func:
                                if command == "break":
                                    end = True
                                    break
                                if command == "reset":
                                    try:
                                        self.reset(
                                            history[
                                                history_number - 2 - history_in_row * 2
                                            ]
                                        )
                                        history_in_row += 1
                                        func_reset = True
                                    except KeyError:
                                        pass
                                else:
                                    if last_command == command:
                                        self.restore(last_command_history[ids[func]])
                                    history_in_row = 0
                                    in_func = True
                                    current_id = func
                                    if func_args is not None:
                                        command(*func_args)
                                    else:
                                        command()
                                    last_command = command
                                    in_func = False
                                self.add_history(window)
                        func_args = None
                        vstup = ""
                    if limit == 0:
                        break
                    if end:
                        break
                self.add_history(window)
        return self

    def add(self, *args):
        for times, arg in enumerate(args):
            times += self.lenght
            setattr(self, f"component_{times}", arg())


class component(builder):
    def __init__(
        self,
        content: list[str],
        y: int,
        x: int,
        height: int | None = None,
        width: int | None = None,
        border: bool = False,
    ):
        self.content = content
        self.y = y
        self.x = x
        if height is None:
            self.height = len(content)
        else:
            self.height = height
        if width is None:
            maxim = 0
            for i in content:
                if len(i) > maxim:
                    maxim = len(i)
            self.width = maxim
        else:
            self.width = width
        self.border = border
        if len(self.content) < self.height and not self.border:
            for i in range(self.height - len(self.content)):
                self.content.append("")
        elif len(self.content) < self.height - 2 and self.border:
            for i in range(self.height - len(self.content) - 2):
                self.content.append("")

    def __call__(self) -> dict:
        window = {"type": "component"}
        if self.border:
            window[self.y] = [self.x, (self.width + 2) * "_"]
            window[self.y + self.height + 1] = [self.x, "|" + (self.width) * "_" + "|"]
        number = 0
        times = 0 if not self.border else 1
        for times in range(self.y + times, self.height + self.y + times):
            if not self.border:
                window[self.y + number] = [
                    self.x,
                    self.content[number]
                    + (self.width - len(self.content[number])) * " ",
                ]
            if self.border:
                window[self.y + number + 1] = [
                    self.x,
                    "|"
                    + self.content[number]
                    + (self.width - len(self.content[number])) * " "
                    + "|",
                ]
            number += 1
        return window


class cinput(builder):
    def __init__(
        self,
        y: int,
        x: int,
        key: str,
        function: dict,
        width=None,
        border: bool = False,
        limit=-1,
        nof=False,
    ):
        self.y = y
        self.x = x
        self.width = width
        self.border = border
        self.key = key
        self.function = function
        self.limit = limit
        self.nof = nof

    def __call__(self) -> dict:
        window = {
            "type": "cinput",
            "key": self.key,
            "x": self.x + 1 if self.border else self.x,
            "y": self.y,
            "border": self.border,
            "function": self.function,
            "width": self.width,
            "limit": self.limit,
            "nof": self.nof,
        }
        width = self.width
        if self.border:
            if width is None:
                window[self.y] = [self.x, (COLS - self.x) * "_"]
                window[self.y + 1] = [self.x, "|" + (COLS - 2 - self.x) * "_" + "|"]
            else:
                window[self.y] = [self.x, (width + 2) * "_"]
                window[self.y + 1] = [self.x, "|" + (width) * "_" + "|"]
        return window
