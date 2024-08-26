import logging

# Support for colored logging: https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# The background is set with 40 plus the number of the color, and the foreground with 30

# These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"


def formatter_message(message, use_color=True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message


COLORS = {"WARNING": RED, "INFO": GREEN, "DEBUG": BLUE, "CRITICAL": YELLOW, "ERROR": RED}


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, date_msg, use_color=True):
        logging.Formatter.__init__(self, msg, date_msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
            if levelname == "ERROR":
                record.msg = COLOR_SEQ % (30 + COLORS[levelname]) + record.msg + RESET_SEQ
        return logging.Formatter.format(self, record)


GRAY_SEQ = COLOR_SEQ % (30 + BLACK)
FORMAT = formatter_message(
    f"[$BOLD%(name)s$RESET|%(levelname)s] {GRAY_SEQ}%(asctime)s.%(msecs)03d{RESET_SEQ}: %(message)s",
)

handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter(FORMAT, "%Y-%m-%d %H:%M:%S"))

logger = logging.getLogger("Edifice")
logger.setLevel(logging.FATAL)
logger.addHandler(handler)
