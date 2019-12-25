#!/usr/bin/env python3
from PySide2 import QtCore
import socket
import logging
import json


class DealerThread(QtCore.QThread):
    dealer_discovered = QtCore.Signal(dict)

    def run(self):

        self._active = True
        self._discovered_dealers = []
        self._last_dealer = None

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.settimeout(0.5)  # TODO: Find a better way to stop the thread

        self._sock.bind(('', 53321))

        logging.info("Listening for dealer annoucements...")

        while self._active:

            try:
                data, addr = self._sock.recvfrom(1500)

            except socket.timeout:
                continue

            except Exception as e:
                logging.debug("Some error happened while waiting for dealear annouce: {}".format(str(e)))
                continue

            if data.find(b"\0") == -1:  # This is redundant
                logging.debug("Malformed dealer annoucement: Missing \\0.")
                continue  # malformed meme

            try:
                msg, signature = data.split(b"\0")
            except ValueError:  # wrong number of values to unpack
                logging.debug("Malformed dealer annoucement: Wrong number of fields")
                continue

            # TODO: Verify signature

            try:
                msg_dict = json.loads(msg.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logging.debug("Malformed dealer annoucement: {}".format(str(e)))
                continue

            if sorted(msg_dict.keys()) != sorted(['fnm', 'addr', 'fqdn']):
                logging.debug("Malformed dealer annoucement: Bad fields")
                continue

            # semantic check

            if msg_dict['addr'] != addr[0]:
                logging.debug("Wrong dealer annoucement: Annouced and source address does not match")
                continue

            if msg_dict['addr'] not in self._discovered_dealers:
                logging.info("Discovered dealer: {} at {}".format(msg_dict['fnm'], msg_dict['addr']))

                self._last_dealer = msg_dict
                self.dealer_discovered.emit(msg_dict)
                self._discovered_dealers.append(msg_dict['addr'])

    def stop(self):
        self._sock.close()
        self._active = False

    def clear(self):
        self._discovered_dealers = []  # We probably don't need a lock here
        self._last_dealer = None  # Here either

    @property
    def last_dealer(self) -> dict:
        return self._last_dealer
