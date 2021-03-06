#!/usr/bin/env python
from __future__ import print_function
import os
from sys import argv
from time import sleep
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import liblo

server_addr = "127.0.0.1:7172"
listen_port = 7173
address = liblo.Address("osc.udp://{}/".format(server_addr))


def run(file_name):
    "Read a file and send its content to /run-code"
    with open(file_name) as f:
        print("Sending {}".format(file_name))
        code = f.read()
        liblo.send(address, "/run-code", code)


def watch(file_name):
    "Return a watchdog observer, it will call the action callback"
    def on_modified(event):
        "File-changed event"
        if not os.path.exists(event.src_path):
            return

        print("Changed {}".format(event.src_path))

        if os.path.samefile(event.src_path, file_name):
            run(file_name)

    print("Started watcher")

    handler = FileSystemEventHandler()
    handler.on_modified = on_modified
    observer = Observer()

    base_path = os.path.split(file_name)[0]
    if not base_path:
        base_path = "."

    observer.schedule(handler, path=base_path)
    observer.daemon = True
    observer.start()

    return observer


def ping():
    "Wait for server response"
    print("Waiting for server response")
    ack = [False]
    server = liblo.Server(listen_port)

    def ack_cb(path, args):
        print("/ack received")
        ack[0] = True

    server.add_method("/ack", None, ack_cb)
    while not ack[0]:
        liblo.send(address, "/ping")
        server.recv(100)


def main_loop():
    "Loop forever and anlde Keyboard Interrupt"
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\rKeyboard Interrupt")


if __name__ == "__main__":
    if len(argv) == 2:
        ping()
        file_name = argv[1]
        run(file_name)
        watcher = watch(file_name)
        main_loop()
        watcher.stop()
