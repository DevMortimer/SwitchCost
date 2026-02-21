import os, time, signal, logging, sys, datetime, ndjson
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


def main() -> None:
    os.makedirs("/tmp/SwitchCost", exist_ok=True)

    setup_logging("/tmp/SwitchCost/SwitchCost.log", also_console=True)
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGHUP, handle_exit)
    logging.info("Running in FOREGROUND mode.")
    run_main_loop()


def show_help():
    print(
        f"\033[1m{bcolors.OKBLUE}SwitchCost{bcolors.ENDC}\n\t\033[1m{bcolors.OKGREEN}help{bcolors.ENDC} - Show this help\n\t\033[1m{bcolors.OKGREEN}status{bcolors.ENDC} - show the current run\n\t{bcolors.WARNING}exit{bcolors.ENDC} - ends the daemon\n"
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        a = sys.argv[1]
        if a == "help":
            show_help()
            exit(0)  # exit early
        elif a == "status":
            # get the current PID
            PID = ""
            try:
                with open("/tmp/SwitchCost/SwitchCost.pid", "r") as file:
                    PID = file.read().strip()
            except FileNotFoundError as e:
                print("no running daemon")
                exit(0)
            # resolve if the PID is running
            try:
                os.kill(int(PID), 0)
            except OSError:
                print("no running daemon")
                exit(0)
            else:
                print("running")
                exit(0)
        elif a == "exit":
            # get the current PID
            PID = ""
            try:
                with open("/tmp/SwitchCost/SwitchCost.pid", "r") as file:
                    PID = file.read().strip()
            except FileNotFoundError as e:
                print("no running daemon; can't exit anything")
                exit(0)
            else:
                try:
                    os.kill(int(PID), 15)
                    print("exited successfully")
                    exit(0)
                except OSError:
                    print("no running daemon; can't exit anything")
                    exit(1)
        else:
            print(f"Unknown command: {a}\n")
            show_help()
            exit(1)

    main()
