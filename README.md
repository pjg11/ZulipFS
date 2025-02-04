# ZulipFS

## Initial setup

[Download a config file for your Zulip instance](https://zulip.com/api/configuring-python-bindings#download-a-zuliprc-file) and save it at `$HOME/.zuliprc`.

```
sudo mkdir /mnt/zulip
sudo chown $USER:$USER /mnt/zulip
python3 -m pip install -r requirements.txt
```

## Usage

```
python3 zulipfs.py /mnt/zulip
```

### List channels

```
ls /mnt/zulip
```

### List topics within a channel 

This only displays topics you've read prior to running this command. To know why, read the accompaniying [blog post](https://pjg1.site/zulipfs#reading-and-knowing-a-file-are-two-different-things).

```
ls /mnt/zulip/<channel>
```

### Read messages of a topic

Displays messages from the time the filesystem was mounted

```
cat /mnt/zulip/<channel>/<topic>
```

### Receive new messages from a topic as they arrive

```
tail -f /mnt/zulip/<channel>/<topic>
```

### Write message to topic

```
echo 'message' >> /mnt/zulip/<channel>/<topic>
```

### Unmount when done

```
umount /mnt/zulip
```

## Limitations
- The current implementation doesn't support the redirection operator `>`, which could be used to create a new topic if it doesn't exist.
- Buggy on macOS: I can read messages fine, but writing works only if I read the message once. And even then, it writes the contents of the entire file (which includes older messages) instead of just the message I passed to it.

## Resources
- [A hand-holding guide to writing FUSE-based filesystems in Python](https://gitlab.com/gunnarwolf/fuse_in_python_guide/-/tree/main)
- [florczakraf/slackfs: Browse and upload slack files directly from your filesystem](https://github.com/florczakraf/slackfs)
