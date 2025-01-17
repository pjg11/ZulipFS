# zulipfs

## Initial setup

Tested on Linux for now

```shell
sudo apt install libfuse2
python -m pip install -r requirements.txt
sudo mkdir /mnt/zulip
sudo chown $USER:$USER /mnt/zulip
```

[Download a config file for Zulip](https://zulip.com/api/configuring-python-bindings#download-a-zuliprc-file) and save it at `~/.zuliprc`.

## Usage

```shell
# Mount filesystem and setup FUSE
python3 zulipfs.py /mnt/zulip
# List channels
ls -al /mnt/zulip
# List topics within a channel
ls -al /mnt/zulip/<channel>
# Read last message of a topic
cat /mnt/zulip/<channel>/<topic>
# Write message to topic
echo 'message' >> /mnt/zulip/<channel>/<topic>
# Unmount when done
umount /mnt/zulip
```

## Limitations
- File/directory metadata is mostly hardcoded and not accurate. I tried setting the modification time and size for the topics when the directory is being listed, but it took too long. The Zulip API returns only the ID of the last message with the topics list. Getting the message itself requires another API call, making it one API call per topic which causes `ls` to hang.
- Reading the last message alone isn't super useful at the moment, and someone suggested being able to run `tail -f` on the file to receive messages as they arrive. This doesn't work at the moment, which I'm looking into.