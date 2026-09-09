import sys, os, select, termios, tty, shutil


def _getkey():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        b = os.read(fd, 1)
        if b == b"\x1b":
            r, _, _ = select.select([fd], [], [], 0.05)
            if r:
                seq = os.read(fd, 2)
                return {"[A": "UP", "[B": "DOWN"}.get(seq.decode(errors="ignore"), "ESC")
            return "ESC"
        if b == b"\x03":
            return "ESC"
        return b.decode(errors="ignore")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def pick(items):
    """Interactive multi-select; returns set of chosen indexes or None if cancelled."""
    if not sys.stdin.isatty():
        return None
    n = len(items)
    if n == 0:
        return None
    cols = max(shutil.get_terminal_size((80, 24)).columns - 6, 30)
    cur, sel = 0, [False] * n
    sys.stdout.write("\x1b[?25l")

    def render():
        rows = []
        for i, t in enumerate(items):
            mark = "\x1b[32m[x]\x1b[0m" if sel[i] else "[ ]"
            row = f" {mark}  {t[:cols]}"
            if i == cur:
                row = "\x1b[7m" + row + "\x1b[0m"
            rows.append(row)
        rows.append(" \x1b[90m↑/↓ move · space toggle · enter done · q cancel\x1b[0m")
        sys.stdout.write("\x1b[0J" + "\n".join(rows) + "\n")
        sys.stdout.flush()

    def erase():
        sys.stdout.write(f"\x1b[{n + 1}A\x1b[0J\x1b[?25h")
        sys.stdout.flush()

    render()
    while True:
        k = _getkey()
        if k in ("q", "x", "Q", "X", "ESC"):
            erase(); return None
        elif k == "UP":
            cur = (cur - 1) % n; sys.stdout.write(f"\x1b[{n + 1}A"); render()
        elif k == "DOWN":
            cur = (cur + 1) % n; sys.stdout.write(f"\x1b[{n + 1}A"); render()
        elif k == " ":
            sel[cur] = not sel[cur]; sys.stdout.write(f"\x1b[{n + 1}A"); render()
        elif k in ("\r", "\n"):
            erase()
            return {i for i, on in enumerate(sel) if on}
        else:
            sys.stdout.write(f"\x1b[{n + 1}A"); render()
