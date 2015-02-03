#!/usr/bin/env python3
# Copyright (c) 2015 Damir Jelić.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys
import tempfile
import mimetypes
import subprocess
import urllib.request
from urllib.parse import urlparse


VIDEO_STREAMER      = 'livestreamer'
YOUTUBE_HANDLER     = 'mpv'

VIDEO_URLS          = ('youtube.com', 'youtu.be', 'www.youtube.com')
STREAM_URLS         = ('www.twitch.tv', 'twitch.tv')


def launch_command(command, args):
    if type(args) is str:
        args = [args]

    return subprocess.call([command] + args)


def launch_browser(url):
    browser = os.getenv('BROWSER')

    if not browser:
        browser = 'rifle'

    return launch_command(browser, url)


def is_terminal():
    # Check if stdin, stdout and stderr are connected to a terminal.
    return sys.stdout.isatty() and sys.stdin.isatty() and sys.stderr.isatty()


def launch_editor(url):
    editor = os.getenv('EDITOR')

    if not editor:
        editor = 'rifle'

    if editor in ('vi', 'vim', 'neovim', 'nano', 'joe') and not is_terminal():
        term = os.getenv('TERMCMD')

        if term and term in ('termite'):
            file_name = download_file(url)

            if file_name:
                return launch_command('termite', ['-e', editor + ' ' + file_name])
            else:
                return -1

        return download_launch_command('rifle', url, '-f t')

    return download_launch_command('rifle', url)


def download_file(url):
    tmp_dir = tempfile.gettempdir()
    tmp_dir = tmp_dir + '/plumber'

    if not os.path.isdir(tmp_dir):
        os.mkdir(tmp_dir)

    fd, file_name = tempfile.mkstemp(prefix='plumber', dir=tmp_dir)

    try:
        os.write(fd, urllib.request.urlopen(url).read())
        os.close(fd)
        return file_name
    except:
        os.close(fd)
        os.remove(file_name)
        return None


def download_launch_command(command, url, args=None):
    file_name = download_file(url)

    if not file_name:
        return -1

    if args:
        if type(args) is str:
            args = [args] + [file_name]
        else:
            args = args + [file_name]
    else:
        args = file_name

    return launch_command(command, args)


def handle_mime(url, mime_type):

    if mime_type.startswith('video/'):
        return launch_command('rifle', url)

    elif mime_type.startswith('image/'):
        return download_launch_command('rifle', url)

    elif mime_type == 'application/pdf':
        return download_launch_command('rifle', url)

    elif mime_type.startswith('text/') and mime_type != 'text/html':
        return launch_editor(url)

    else:
        return launch_browser(url)


def lookup_content_type(url):
    request = urllib.request.Request(url=url, method='HEAD')

    try:
        request = urllib.request.urlopen(request)
        response = request.getheader('Content-Type')
    except:
        return None, None

    if ';' in response:
        content_type, encoding = response.split(';', maxsplit=1)
        return content_type, encoding.strip()

    return response, None


def find_mime_type(url):
    path = url.path
    url = url.geturl()

    mime_type, encoding = mimetypes.guess_type(url)

    if not mime_type:
        mime_type, encoding = mimetypes.guess_type(path)

    if not mime_type:
        mime_type, encoding = lookup_content_type(url)

    return mime_type


def main():
    if len(sys.argv) != 2:
        return -1

    try:
        url = urlparse(sys.argv[1])
    except:
        return -1

    url_string = url.geturl()

    if url.netloc in (VIDEO_URLS):
        return launch_command(YOUTUBE_HANDLER, url_string)

    elif url.netloc in (STREAM_URLS):
        return launch_command(VIDEO_STREAMER, url_string)

    mime_type = find_mime_type(url)

    if mime_type:
        return handle_mime(url_string, mime_type)

    return launch_browser(url_string)


if __name__ == '__main__':
    main()
