#!/usr/bin/env python3

import os, emoji, errno, stat, sys, fuse, time, zulip
from datetime import datetime

fuse.fuse_python_api = (0, 2)

class ZulipFS(fuse.Fuse):

    def __init__(self):
        fuse.Fuse.__init__(self)
        self.client = zulip.Client(config_file="~/.zuliprc")
        self.channels = { self.file_name(i['name']): i for i in self.client.get_streams()['streams'] }
        self.topics = {i: {} for i in self.channels.keys()}

    def file_name(self, name):
        return emoji.demojize(name.replace('/', '%2F'))

    def zulip_name(self, name):
        return emoji.emojize(name.replace('%2F', '/'))

    def get_topic(self, channel, topic):
        request = {
            "anchor": "newest",
            "num_before": 1,
            "num_after": 0,
            "narrow": [
                {"operator": "channel", "operand": self.channels[channel]['name']},
                {"operator": "topic", "operand": self.zulip_name(topic)},
            ],
            "apply_markdown": False,
        }
        try:
            message = self.client.get_messages(request)['messages'][0]

            timestamp = float(message['timestamp'])
            message_fmt = f"""[{datetime.fromtimestamp(message['timestamp'])}] {message['sender_full_name']}
{message['content']}
""".encode()

            if topic not in self.topics[channel]:
                # First message in file
                self.topics[channel][topic] = {
                    'last_message': message_fmt,
                    'last_timestamp': timestamp,
                }
            else:
                # Subsequent messages appended to file
                if timestamp > self.topics[channel][topic]['last_timestamp']:
                    self.topics[channel][topic] = {
                        'last_message': self.topics[channel][topic]['last_message'] + b"\n" + message_fmt,
                        'last_timestamp': timestamp,
                    }

        except IndexError:
            # topic doesn't exist
            pass

        return self.topics[channel][topic]

    def readdir(self, path, offset):
        dirents = [ '.', '..' ]
        if path == '/':
            dirents.extend(self.channels.keys())
        else:
            dirents.extend(self.topics[path[1:]].keys())

        for r in dirents:
            yield fuse.Direntry(r)

    def getattr(self, path):
        st = fuse.Stat()
        if path == "/" or path[1:] in self.channels.keys():
            # channel/directory
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
            st.st_size = 4096
            st.st_mtime = time.time()
        else:
            # topic/file
            try:
                channel, topic = path[1:].split('/')
                t = self.get_topic(channel, topic)
                st.st_mode = stat.S_IFREG | 0o644
                st.st_nlink = 1
                st.st_size = len(t['last_message'])
                st.st_mtime = t['last_timestamp']
            except ValueError:
                return -errno.ENOENT

        st.st_atime = st.st_mtime
        st.st_ctime = st.st_mtime
        st.st_uid = os.getuid()
        st.st_gid = os.getgid()
        return st

    def read(self, path, size, offset):
        try:
            channel, topic = path[1:].split('/')
            t = self.get_topic(channel, topic)
            return t['last_message']
        except ValueError:
            return -errno.ENOENT

    def write(self, path, body, offset):
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
