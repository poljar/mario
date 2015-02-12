#!/usr/bin/env python3
# Copyright (c) 2015 Damir Jelić.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import re
import sys
import argparse
import tempfile
import mimetypes
import subprocess
import configparser
import logging as log
import urllib.request

from functools import reduce
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse


def domain_is_func(msg, arguments, match_group):
    return msg['netloc'] in arguments, msg, match_group


def content_is_func(msg, arguments, match_group):
    t, _ = mimetypes.guess_type(msg['data'])

    try:
        return t in arguments, msg, match_group
    except TypeError:
        return False, msg, match_group


def type_is_func(msg, arguments, match_group):
    url = urlparse(msg['data'])
    is_url = bool(url.scheme)

    if arguments == 'text' and not is_url:
        return True, msg, match_group
    elif arguments == 'url' and is_url:
        msg['netloc'] = url.netloc
        msg['netpath'] = url.path
        return True, msg, match_group
    else:
        return False, msg, match_group


def data_is_func(msg, arguments, match_group):
    return msg['data'] in arguments, msg, match_group


def data_match_func(msg, arguments, match_group):
    m = None

    print(msg)
    for pattern in arguments.split('\n'):
        m = re.search(pattern, msg['data'])

        if not m:
            return False, msg, ()

    if m.groups():
        return True, msg, m.groups()
    else:
        return True, msg, (m.group(),)


def data_rewrite_func(msg, arguments, match_group):
    f = lambda acc, r: acc.replace(*(r.split(',', 2)))

    msg['data'] = reduce(f, arguments.split('\n'), msg['data'])

    return True, msg, match_group


def plumber_open_func(msg, arguments, match_group):
    print(msg, match_group)
    tmp = arguments.format(*match_group, **msg)
    print(tmp)
#    return subprocess.call(tmp.split())

def arg_is_func(msg, arguments, match_group):
    arg, check = arguments.split()

    if arg.format(*match_group, **msg) == check:
        return True, msg, match_group

match_rules = {
        'arg is'       : arg_is_func,
        'type is'      : type_is_func,
        'data is'      : domain_is_func,
        'domain is'    : domain_is_func,
        'content is'   : content_is_func,
        'data matches' : data_match_func,
        'data rewrite' : data_rewrite_func,
}

action_rules = {
        'plumber open' : plumber_open_func,
}


def handle_rules(msg, config):
    rule_matched = False

    for rule in config.sections():

        match_group = ()
        options = config.options(rule)

        match_options  = [opt for opt in options if opt in match_rules]
        action_options = [opt for opt in options if opt in action_rules]

        for opt in match_options:
            f = match_rules[opt]
            res, msg, match_group = f(msg, config.get(rule, opt), match_group)

            if not res:
                rule_matched = False
                break

            rule_matched = True

        if rule_matched:
            for opt in action_options:
                f = action_rules[opt]
                msg = f(msg, config.get(rule, opt), match_group)

            break


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-v', '--verbose', help='turn on verbose mode',
                        action='store_true')
    parser.add_argument('msg', help='message to handle', type=str)

    args = parser.parse_args()

    if args.verbose:
        log.basicConfig(format='%(levelname)s: %(message)s', level=log.DEBUG)
    else:
        log.basicConfig(format='%(levelname)s: %(message)s')

    config = configparser.ConfigParser()
    config.read('example.ini')

    config.remove_section('mario')

    handle_rules({'data' : args.msg}, config)

if __name__ == '__main__':
    main()
