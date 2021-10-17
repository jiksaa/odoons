class Colors:
    """
    sources: https://www.geeksforgeeks.org/print-colors-python-terminal/

    Colors class:reset all colors with colors.reset;
    two sub classes fg for foreground and bg for background;
    use as colors.subclass.colorname.

    i.e. colors.fg.red or colors.bg.greenalso, the generic bold, disable,
    underline, reverse, strike through,
    and invisible work with the main class i.e. colors.bold
    """

    reset = "\033[0m"
    bold = "\033[01m"
    disable = "\033[02m"
    underline = "\033[04m"
    reverse = "\033[07m"
    strikethrough = "\033[09m"
    invisible = "\033[08m"

    class fg:
        black = "\033[30m"
        red = "\033[31m"
        green = "\033[32m"
        orange = "\033[33m"
        blue = "\033[34m"
        purple = "\033[35m"
        cyan = "\033[36m"
        lightgrey = "\033[37m"
        darkgrey = "\033[90m"
        lightred = "\033[91m"
        lightgreen = "\033[92m"
        yellow = "\033[93m"
        lightblue = "\033[94m"
        pink = "\033[95m"
        lightcyan = "\033[96m"

    class bg:
        black = "\033[40m"
        red = "\033[41m"
        green = "\033[42m"
        orange = "\033[43m"
        blue = "\033[44m"
        purple = "\033[45m"
        cyan = "\033[46m"
        lightgrey = "\033[47m"


def next_muted():
    print(Colors.fg.lightgrey)


def reset():
    print(Colors.reset)


def info(msg):
    print("{}{}{}".format(Colors.bold, msg, Colors.reset))


def success(msg):
    print("{}{}{}".format(Colors.bold, msg, Colors.reset))


def warning(msg):
    print("{}{}{}".format(Colors.fg.orange, msg, Colors.reset))


def error(msg):
    print("{}{}{}".format(Colors.fg.red, msg, Colors.reset))


def debug(msg):
    print("{}{}{}".format(Colors.fg.purple, msg, Colors.reset))
