import os, time, signal, logging, sys, datetime, ndjson, atexit
import tracker
from logging.handlers import RotatingFileHandler


class bcolors:
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


running = True


def setup_logging(log_path: str, also_console: bool) -> None:
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s %(levelname)s pid=%(process)d %(message)s")
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    if also_console:
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        logger.addHandler(console)


def handle_exit(signum, frame) -> None:
    global running
    logging.info("Signal received: %s. Shutting down.", signum)
    running = False


def run_main_loop():
    logging.info("Daemon started. Entering main loop.")

    while running:
        time.sleep(0.2)
        current_program = tracker.check_current_program()
        if tracker.current_prog != current_program:
            filepath = "/tmp/SwitchCost/events.ndjson"
            now = datetime.datetime.today()
            last = tracker.get_last_timestamp(filepath)

            with open(filepath, "a") as f:
                writer = ndjson.writer(f)
                writer.writerow(
                    {
                        "timestamp": str(now),
                        "from": tracker.current_prog,
                        "to": current_program,
                        "duration": str(now - tracker.get_last_timestamp(filepath))
                        if last
                        else "0",
                    }
                )
                tracker.current_prog = current_program

    logging.info("Cleanup done. Exiting.")


def check_already_running():
    pidfile = "/tmp/SwitchCost/SwitchCost.pid"
    try:
        with open(pidfile, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (FileNotFoundError, ValueError, OSError):
        pass
    return False


def write_pid():
    pidfile = "/tmp/SwitchCost/SwitchCost.pid"
    with open(pidfile, "w") as f:
        f.write(str(os.getpid()))


def remove_pid():
    pidfile = "/tmp/SwitchCost/SwitchCost.pid"
    try:
        os.remove(pidfile)
    except FileNotFoundError:
        pass


def main() -> None:
    os.makedirs("/tmp/SwitchCost", exist_ok=True)

    if check_already_running():
        print("SwitchCost is already running")
        sys.exit(1)

    write_pid()
    atexit.register(remove_pid)

    setup_logging("/tmp/SwitchCost/SwitchCost.log", also_console=True)
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGHUP, handle_exit)
    logging.info("Running in FOREGROUND mode.")
    run_main_loop()
    remove_pid()


def show_stats():
    filepath = "/tmp/SwitchCost/events.ndjson"
    try:
        with open(filepath, "r") as f:
            events = list(ndjson.reader(f))
    except FileNotFoundError:
        print("No events recorded yet")
        return

    if not events:
        print("No events recorded yet")
        return

    totals = {}
    for event in events:
        prog = event.get("to", "Unknown")
        dur_str = event.get("duration", "0")
        try:
            if dur_str == "0":
                continue
            parts = dur_str.split(":")
            if len(parts) == 3:
                h, m, s = parts
                seconds = int(h) * 3600 + int(m) * 60 + float(s)
            else:
                seconds = float(dur_str)
        except (ValueError, AttributeError):
            seconds = 0
        totals[prog] = totals.get(prog, 0) + seconds

    if not totals:
        print("No duration data")
        return

    print(f"\n{bcolors.OKBLUE}Time per program:{bcolors.ENDC}")
    for prog, secs in sorted(totals.items(), key=lambda x: x[1], reverse=True):
        h = int(secs // 3600)
        m = int((secs % 3600) // 60)
        s = int(secs % 60)
        print(f"  {prog}: {h}h {m}m {s}s")
    print(f"\nTotal switches: {len(events)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        a = sys.argv[1]
        if a == "status":
            show_stats()
            exit(0)
        elif a == "exit":
            print("Sending exit signal...")
            os.kill(os.getpid(), signal.SIGTERM)
            exit(0)
        else:
            print(f"Unknown command: {a}")
            print(f"Usage: python main.py [status|exit]")
            exit(1)

    main()
