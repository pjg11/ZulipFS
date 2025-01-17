#!/usr/bin/env python3

import os, errno, stat, sys, fuse, time, zulip
from datetime import datetime

fuse.fuse_python_api = (0, 2)

class ZulipFS(fuse.Fuse):

    def __init__(self):
        fuse.Fuse.__init__(self)
        self.client = zulip.Client(config_file="~/.zuliprc")
        self.channels = { self.normalize(i['name']): i for i in self.client.get_streams()['streams'] }
        self.topics = {}

    def normalize(self, name):
        return name.replace('/', '%2F')

    def get_topics(self, channel):
        if channel not in self.topics:
            # setting the limit of topics to 50
            topicslist = self.client.get_stream_topics(self.channels[channel]['stream_id'])['topics'][:50]
            self.topics[channel] = { self.normalize(t['name']): t for t in topicslist }
        return self.topics[channel]

    def readdir(self, path: str, offset: int):
        contents = [ '.', '..' ]
        if path == '/':
            contents.extend(self.channels.keys())
        else:
            channel = path[1:]
            if channel in self.channels:
                self.get_topics(channel)
                contents.extend(self.topics[channel].keys())

        for r in contents:
            yield fuse.Direntry(r)

    def getattr(self, path: str) -> fuse.Stat:
        st = fuse.Stat()
        now = time.time()

        dirs = [ '/%s' % i for i in self.channels.keys() ]
        dirs.extend('/')

        if path in dirs:
            st.st_mode = stat.S_IFDIR | 0o555
            st.st_nlink = 2
            st.st_atime = now
            st.st_atime = now
            st.st_atime = now
            return st

        channel, topic = path[1:].split('/')
        try:
            try:
                timestamp = self.topics[channel][topic]['last_timestamp']
            except KeyError:
                timestamp = now

            st.st_mode = stat.S_IFREG | 0o666
            st.st_nlink = 1

            try:
                st.st_size = len(self.topics[channel][topic]['last_message']) + 1
            except KeyError:
                st.st_size = 65535

            st.st_atime = timestamp
            st.st_mtime = timestamp
            st.st_ctime = timestamp
            return st
        except ValueError:
            return -errno.ENOENT

        return -errno.ENOENT

    def read(self, path: str, size: int, offset: int) -> bytes:
        channel, topic = path[1:].split('/')
        try:
            self.get_topics(channel)

            last_message = self.client.get_raw_message(self.topics[channel][topic]['max_id'])
            self.topics[channel][topic]['last_message'] = f"""[{datetime.fromtimestamp(last_message['message']['timestamp'])}] {last_message['message']['sender_full_name']}
{last_message['raw_content']}
"""
            self.topics[channel][topic]['last_timestamp'] = float(last_message['message']['timestamp'])

            return self.topics[channel][topic]['last_message'].encode()
        except ValueError:
            return -errno.ENOENT

    def write(self, path: str, body: bytes, offset: int):
        channel, topic = path[1:].split('/')
        request = {
            "type": "stream",
            "to": channel,
            "topic": topic,
            "content": body.decode(),
        }
        self.client.send_message(request)
        return len(body)

if __name__ == '__main__':
    server = ZulipFS()
    server.parse(errex=1)
    server.main()
