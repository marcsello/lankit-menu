#!/usr/bin/env python3
import requests
import json
import logging

ACCEPTED_INDEX_VERSIONS = ["0.2"]
CONNECTION_TIMEOUT = 2


class IndexVersionError(Exception):
    pass


class GameIndex(object):

    def __init__(self, host):
        self._host = host
        self._index = {}

    def load(self):
        self._index = {}

        logging.info("Loading game index...")

        response = requests.get(self._host + "/index.json", timeout=CONNECTION_TIMEOUT)
        response.raise_for_status()

        index = json.loads(response.content.decode('utf-8'))

        logging.debug("Index Dump: {}".format(json.dumps(index)))

        # run some checks

        if index['version'] not in ACCEPTED_INDEX_VERSIONS:
            logging.error("{} is not supported index version".format(index['version']))
            raise IndexVersionError()

        # If everything went fine:
        self._index = index

        logging.info("Loaded index containing {} entries".format(self.gameCount))

    def getGameList(self):
        return {k: v['name'] for k, v in self._index['games'].items()}

    def getGameInfo(self, _id):  # we use strings defined by the maintainer to identify games
        return self._index["games"][_id]

    @property
    def isLoaded(self):
        return self._index is not None

    @property
    def maintainer(self):
        if not self._index:
            return ""

        try:
            return self._index['maintainer']
        except KeyError:
            return "Not provided"

    @property
    def host_friendlyname(self):
        if not self._index:
            return ""

        try:
            return self._index['host_friendlyname']
        except KeyError:
            return "Not provided"

    @property
    def banner_url(self):

        if not self._index:
            return None

        try:
            return self._index['banner']
        except KeyError:
            return None

    @property
    def gameCount(self):
        return len(self._index['games'])

    @property
    def rawGameIndex(self):
        return self._index


