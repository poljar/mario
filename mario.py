#!/usr/bin/env python3
# Copyright (c) 2015 Damir Jelić, Denis Kasak
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

def get_var_references(s):
    tokens = s.split()
    return (t for t in tokens if t[0] == '{' and t[-1] == '}')

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


def arg_is_func(msg, arguments, match_group):
    arg, checks = arguments.split(maxsplit=1)

    return arg.format(*match_group, **msg) in checks.split('\n'), msg, match_group


def data_is_func(msg, arguments, match_group):
    return arg_is_func(mgs, '{data} ' + arguments, match_group)


def arg_matches_func(msg, arguments, match_group):
    arg, patterns = arguments.split(maxsplit=1)
    arg = arg.format(*match_group, **msg)

    for pattern in patterns.split('\n'):
        m = re.search(pattern, arg)

        if not m:
            return False, msg, ()

    if m.groups():
        return True, msg, m.groups()
    else:
        return True, msg, (m.group(),)


def data_match_func(msg, arguments, match_group):
    return arg_matches_func(msg, '{data} ' + arguments, match_group)


def arg_rewrite_func(msg, arguments, match_group):
    arg, patterns = arguments.split(maxsplit=1)
    tmp = arg.format(*match_group, **msg)
    arg = arg.strip('{}')

    f = lambda acc, pattern: acc.replace(*pattern.split(',', 2))
    tmp = reduce(f, patterns.split('\n'), tmp)

    msg[arg] = tmp

    return True, msg, match_group


def data_rewrite_func(msg, arguments, match_group):
    return arg_rewrite_func(msg, '{data} ' + arguments, match_group)


def content_is_func(msg, arguments, match_group):
    t, _ = mimetypes.guess_type(msg['data'])

    try:
        return t in arguments, msg, match_group
    except TypeError:
        return False, msg, match_group


def plumb_open_func(msg, arguments, match_group):
    tmp = arguments.format(*match_group, **msg)

    vs = get_var_references(arguments)
    for v in vs:
        var_name = v.strip('{}')
        log.info('\t{var} = {value}'.format(var=v, value=msg[var_name]))
#    return subprocess.call(tmp.split())


def plumb_download_func(msg, arguments, match_group):
    pass


match_rules = {
        'type is'      : type_is_func,
        'arg is'       : arg_is_func,
        'data is'      : data_is_func,
        'arg matches'  : arg_matches_func,
        'data matches' : data_match_func,
        'arg rewrite'  : arg_rewrite_func,
        'data rewrite' : data_rewrite_func,
        'content is'   : content_is_func,
}

action_rules = {
        'plumb open'     : plumb_open_func,
        'plumb download' : plumb_download_func,
}


def handle_rules(msg, config):
    rule_matched = False

    log.info('Matching message against rules.')
    for rule in config.sections():

        log.debug('Matching against rule [%s]', rule)

        match_group = ()
        options = config.options(rule)

        match_options  = (opt for opt in options if opt in match_rules)
        action_options = (opt for opt in options if opt in action_rules)

        for opt in match_options:
            f = match_rules[opt]
            res, msg, match_group = f(msg, config.get(rule, opt), match_group)

            if not res:
                rule_matched = False
                break

            rule_matched = True

        if rule_matched:
            log.info('Rule [%s] matched.', rule)
            for opt in action_options:
                action = config.get(rule, opt)
                log.info('Executing action "%s" for rule [%s].', action, rule)
                f = action_rules[opt]
                msg = f(msg, action, match_group)

            break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='count',
                        help='increase log verbosity level (pass multiple times)')
    parser.add_argument('msg', help='message to handle', type=str)

    args = parser.parse_args()

    verbosity = log.DEBUG

    if args.verbose:
        log_levels = {
            1 : log.WARNING,
            2 : log.INFO,
            3 : log.DEBUG
        }
        try:
            verbosity = log_levels[args.verbose]
        except KeyError:
            verbosity = log.DEBUG

    if args.verbose:
        log.basicConfig(format='%(levelname)s: %(message)s', level=verbosity)
    else:
        log.basicConfig(format='%(levelname)s: %(message)s')

    config = configparser.ConfigParser()
    config.read('example.ini')
    log.info('Config parsed.')

    config.remove_section('mario')

    handle_rules({'data' : args.msg}, config)

if __name__ == '__main__':
    main()
