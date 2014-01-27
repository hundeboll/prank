#!/usr/bin/env python2

import argparse
import inspect
import logging
import pickle
import socket
import struct
import sys
import imp

logger = logging.getLogger(__file__)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

p = argparse.ArgumentParser()

p.add_argument('-o', '--host',
        type=str,
        default="localhost")

p.add_argument('-p', '--port',
        type=int,
        default='15885')

p.add_argument('-v', '--verbose',
        action='store_true')

p.add_argument('-d', '--debug',
        action='store_true')

args = p.parse_args()

class server(object):
    hdr_len = 4

    def __init__(self, address, port):
        self.running = True
        self.sock = None
        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind((address, port))
        self.srv.listen(1)

    def run(self):
        while self.running:
            try:
                sock = None
                sock,client = self.srv.accept()
                logger.info("new connection: {}".format(client))
                self.sock = sock
                self.client = client

                if not self.read_source():
                    continue

                if not self.read_object():
                    continue

                self.run_object()
                self.read_ending()
                self.write_result()
                self.close_client()
                logger.info("closed connection")
            except Exception as e:
                logger.error("exception: {}".format(e))

    def read_hdr(self):
        l = 0
        data = bytes()

        while l < self.hdr_len:
            d = self.sock.recv(self.hdr_len - l)
            l += len(d)
            data += d

            if not d:
                return None

        length, = struct.unpack(">I", data)

        return length

    def read_data(self):
        length = self.read_hdr()
        if not length:
            return None

        l = 0
        data = bytes()

        while l < length:
            d = self.sock.recv(length - l)
            l += len(d)

            if not d:
                return

            data += d

        return data

    def read_source(self):
        data = self.read_data()
        if not data:
            return False

        src = pickle.loads(data)
        logger.debug("read source with length {}".format(len(src)))
        module = imp.new_module("client")
        exec src in module.__dict__

        for name,obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                logger.debug("adding global: {}".format(name))
                globals()[name] = obj

        sys.modules[name] = module

        return True

    def read_object(self):
        data = self.read_data()
        if not data:
            return False

        logger.debug("read object with length {}".format(len(data)))
        self.obj = pickle.loads(data)

        return True

    def run_object(self):
        logger.info("running object")
        self.obj.run()

    def read_ending(self):
        data = self.read_data()
        logger.debug("controller requested ending")

    def write_result(self):
        res = self.obj.result()
        logger.info("sending result with length {}".format(len(res)))
        res = pickle.dumps(res)
        self.sock.send(res)

    def close_client(self):
        if not self.sock:
            return

        self.sock.shutdown(socket.SHUT_WR)
        self.sock.close()
        self.sock = None

    def close_srv(self):
        if not self.srv:
            return

        self.close_client()
        self.srv.close()
        self.srv = None

class client(object):
    def __init__(self, host, port, obj):
        mod = inspect.getmodule(obj)
        src = inspect.getsource(mod)

        self.sock = socket.create_connection((host, port))

        self.write(src)
        self.write(obj)

    def write(self, data=None):
        if not data:
            hdr = struct.pack(">I", 0)
            self.sock.send(hdr)
            return

        obj = pickle.dumps(data)
        hdr = struct.pack(">I", len(obj))
        self.sock.send(hdr)
        self.sock.send(obj)

    def read(self):
        data = bytes()
        while True:
            d = self.sock.recv(2048)

            if not d:
                break

            data += d

        return pickle.loads(data)


if __name__ == "__main__":
    if args.verbose:
        logger.setLevel(logging.INFO)

    if args.debug:
        logger.setLevel(logging.DEBUG)

    try:
        s = server(args.host, args.port)
        s.run()
    except KeyboardInterrupt:
        s.close_srv()
