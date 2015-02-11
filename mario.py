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


def domain_is_func(data, arguments, match_group):
    url = urlparse(data)

    return url.netloc in arguments, match_group


def content_is_func(data, arguments, match_group):
    t, _ = mimetypes.guess_type(data)

    try:
        return t in arguments, match_group
    except TypeError:
        return False, match_group


def type_is_func(data, arguments, match_group):
    url = urlparse(data)
    is_url = bool(url.scheme)

    if arguments == 'text' and not is_url:
        return True, match_group
    elif arguments == 'url' and is_url:
        return True, match_group
    else:
        return False, match_group


def data_is_func(data, arguments, match_group):
    return data in arguments, match_group


def data_match_func(data, arguments, match_group):
    m = None

    print(data)
    for pattern in arguments.split('\n'):
        pattern = '(' + pattern + ')'
        m = re.search(pattern, data)

        if not m:
            return False, ()

    return True, m.groups()


def data_rewrite_func(data, arguments, match_group):
    f = lambda acc, r: acc.replace(*(r.split(',', 2)))

    return reduce(f, arguments.split('\n'), data)


def plumber_open_func(data, arguments, match_group):
    tmp = arguments.format(*match_group, data=data)
    print(tmp)
    return subprocess.call(tmp.split())


match_rules = {
        'type is'      : type_is_func,
        'data is'      : domain_is_func,
        'domain is'    : domain_is_func,
        'content is'   : content_is_func,
        'data matches' : data_match_func,
}

action_rules = {
        'data rewrite' : data_rewrite_func,
        'plumber open' : plumber_open_func,
}


def handle_rules(data, config):
    rule_matched = False

    for rule in config.sections():

        match_group = ()
        options = config.options(rule)

        match_options = list(filter((lambda opt: opt in match_rules),
                            options))
        action_options = list(filter((lambda opt: opt in action_rules),
                            options))

        for opt in match_options:
            f = match_rules[opt]
            res, match_group = f(data, config.get(rule, opt), match_group)

            if not res:
                rule_matched = False
                break

            rule_matched = True

        if rule_matched:
            for opt in action_options:
                f = action_rules[opt]
                data = f(data, config.get(rule, opt), match_group)

            break


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-v', '--verbose', help='turn on verbose mode',
                        action='store_true')
    parser.add_argument('data', help='Data to handle', type=str)

    args = parser.parse_args()

    if args.verbose:
        log.basicConfig(format='%(levelname)s: %(message)s', level=log.DEBUG)
    else:
        log.basicConfig(format='%(levelname)s: %(message)s')

    config = configparser.ConfigParser()
    config.read('example.ini')

    config.remove_section('mario')

    handle_rules(args.data, config)

if __name__ == '__main__':
    main()
