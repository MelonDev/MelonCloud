from typing import Any, Generator


class Colors:
    # HEADER = '\033[95m'
    blue = '\033[94m'
    cyan = '\033[96m'
    green = '\033[92m'
    yellow = '\033[93m'
    red = '\033[91m'
    white = '\033[0m'

    message = None

    # BOLD = '\033[1m'
    # UNDERLINE = '\033[4m'

    def __str__(self):
        if self.message is not None:
            return self.message

    def __init__(self, color: str, message: Any):
        self.message = color + str(message) + Colors.white

    def c(color: str, message: Any) -> str:
        return color + str(message) + Colors.white


class log:
    def e(self: Any):
        print(Colors.red + str(self) + Colors.white)

    def w(self: Any):
        print(Colors.yellow + str(self) + Colors.white)

    def i(self: Any):
        print(Colors.blue + str(self) + Colors.white)

    def m(*args, color: str):
        pack = color + '{}' + Colors.white
        args = (pack.format(i) for i in args)
        print(*args)
