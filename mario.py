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
import magic
from xdg import BaseDirectory
from enum import Enum
from functools import reduce
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

class Kind(Enum):
    blob = 1
    url = 2


def get_var_references(s):
    tokens = s.split()
    return (t for t in tokens if t[0] == '{' and t[-1] == '}')


def kind_is_func(msg, arguments, match_group):
    try:
        return msg['kind'] == Kind[arguments], msg, match_group
    except KeyError:
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


def data_istype_func(msg, arguments, match_group):
    if msg['kind'] == Kind.url:
        t, _ = mimetypes.guess_type(msg['data'])
    elif msg['kind'] == Kind.blob:
        t = magic.from_buffer(msg['data'])
    else:
        pass

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
        'kind is'      : kind_is_func,
        'arg is'       : arg_is_func,
        'data is'      : data_is_func,
        'data istype'  : data_istype_func,
        'arg matches'  : arg_matches_func,
        'data matches' : data_match_func,
        'arg rewrite'  : arg_rewrite_func,
        'data rewrite' : data_rewrite_func,
}

action_rules = {
        'plumb open'     : plumb_open_func,
        'plumb download' : plumb_download_func,
}


def handle_rules(msg, config):
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
        else:
            rule_matched = True

        if rule_matched:
            log.info('Rule [%s] matched.', rule)
            for opt in action_options:
                action = config.get(rule, opt)
                log.info('Executing action "%s" for rule [%s].', action, rule)
                f = action_rules[opt]
                res, msg, match_group = f(msg, action, match_group)
                if not res:
                    break
            break
    else:
        log.info('No rule matched.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='count',
                        help='increase log verbosity level (pass multiple times)')
    parser.add_argument('msg', help='message to handle', type=str)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('kind', help='kind of message',
                        nargs='?',
                        type=lambda n: Kind[n],
                        choices=[k for k in Kind])
    group.add_argument('--guess',  action='store_true',
                       help='guess the kind of the message')

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

    if args.guess:
        log.info("Using heuristics to guess kind...")
        url = urlparse(args.msg)
        if url.scheme:
            args.kind = Kind.url
        else:
            args.kind = Kind.blob
        log.info("\tGuessed kind {}".format(args.kind))

    msg = {'data' : args.msg,
           'kind' : args.kind
          }

    if args.kind == Kind.url:
        url = urlparse(args.msg)
        msg['netloc'] = url.netloc
        msg['netpath'] = url.path

    config = configparser.ConfigParser()
    config_path = os.path.join(BaseDirectory.xdg_config_home, 'mario', 'example.ini')
    log.info('Using config file {}'.format(config_path))
    config.read(config_path)
    log.info('Config parsed.')

    config.remove_section('mario')

    handle_rules(msg, config)


if __name__ == '__main__':
    main()
