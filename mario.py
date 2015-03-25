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

from parser import make_parser, parse_rule_file

class Kind(Enum):
    raw = 1
    url = 2

def lookup_content_type(url):
    request = urllib.request.Request(url=url, method='HEAD')

    try:
        request = urllib.request.urlopen(request)
        response = request.getheader('Content-Type')
    except (HTTPError, URLError):
        return None, None

    if ';' in response:
        content_type, encoding = response.split(';', maxsplit=1)
        return content_type, encoding.strip()

    return response, None

def get_var_references(s):
    tokens = s.split()
    return (t for t in tokens if t[0] == '{' and t[-1] == '}')


def kind_is_func(msg, arguments, match_group):
    try:
        return msg['kind'] == Kind[arguments[0]], msg, match_group
    except KeyError:
        return False, msg, match_group


def arg_is_func(msg, arguments, match_group):
    arg, checks = arguments

    ret = arg.format(*match_group, **msg) in checks
    return ret, msg, match_group


def data_is_func(msg, arguments, match_group):
    return arg_is_func(mgs, '{data} ' + arguments, match_group)


def arg_matches_func(msg, arguments, match_group):
    arg, patterns = arguments
    arg = arg.format(*match_group, **msg)

    for pattern in patterns:
        m = re.search(pattern, arg)

        if m:
            return True, msg, match_group + m.groups()
    else:
        return False, msg, match_group


def data_match_func(msg, arguments, match_group):
    return arg_matches_func(msg, '{data} ' + arguments, match_group)


def arg_rewrite_func(msg, arguments, match_group):
    arg, patterns = arguments
    tmp = arg.format(*match_group, **msg)
    arg = arg.strip('{}')

    f = lambda acc, pattern: acc.replace(*pattern.split(',', 2))
    tmp = reduce(f, patterns, tmp)

    msg[arg] = tmp

    return True, msg, match_group


def data_rewrite_func(msg, arguments, match_group):
    return arg_rewrite_func(msg, '{data} ' + arguments, match_group)


def mime_from_buffer(buf):
    try:
        # magic returns the mimetype as bytes, hence the decode
        t = magic.from_buffer(buf, mime=True).decode('utf-8')
    except AttributeError:
        try:
            m = magic.open(magic.MIME)
            m.load()
            t, _ = m.buffer(buf.encode('utf-8')).split(';')
        except AttributeError as e:
            log.error('Your \'magic\' module is unsupported. ' + \
                    'Install either https://github.com/ahupp/python-magic ' + \
                    'or https://github.com/file/file/tree/master/python ' + \
                    '(official \'file\' python bindings, available as the ' + \
                    'python-magic package on many distros)')

            raise SystemExit

    return t


def arg_istype_func(msg, arguments, match_group):
    arg, patterns = arguments
    arg = arg.format(*match_group, **msg)

    if msg['kind'] == Kind.url:
        t, _ = mimetypes.guess_type(arg)

        if not t:
            log.debug('Failed mimetype guessing... Trying Content-Type header.')
            t, _ = lookup_content_type(arg)
    elif msg['kind'] == Kind.raw:
        t = mime_from_buffer(arg)
    else:
        pass

    if t:
        for pattern in patterns:
            m = re.search(pattern, t)

            if m:
                break
    else:
        log.info("Couldn't determine mimetype.")
        return False, msg, match_group

    if m:
        log.debug('\tType matches: {}'.format(m.group()))
        return bool(m), msg, match_group
    else:
        log.debug('\tType doesn\'t match or cannot guess type.')
        return False, msg, match_group


def data_istype_func(msg, arguments, match_group):
    return arg_istype_func(msg, '{data} ' + arguments, match_group)


def plumb_open_func(msg, arguments, match_group):
    tmp = arguments.format(*match_group, **msg)

    vs = get_var_references(arguments)
    for v in vs:
        var_name = v.strip('{}')
        log.info('\t\t{var} = {value}'.format(var=v, value=msg[var_name]))

    ret = subprocess.call(tmp.split())
    if ret == 0:
        return True, msg, match_group
    else:
        log.info('\t\tTarget program exited with non-zero exit code ({})'.format(ret))
        return False, msg, match_group


def plumb_download_func(msg, arguments, match_group):
    if msg['kind'] != Kind.url:
        return False, msg, match_group

    user_agent = 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0'

    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', user_agent)]

    tmp_dir = tempfile.gettempdir()

    try:
        with tempfile.NamedTemporaryFile(prefix='plumber-', dir=tmp_dir, delete=False) as f:
            f.write(opener.open(msg['data']).read())
            msg['filename'] = f.name
            return True, msg, match_group
    except OSError as e:
        log.info('Error downloading file: ' + str(e))
        return False, msg, match_group


match_rules = {
        'kind is'      : kind_is_func,
        'arg is'       : arg_is_func,
        'arg istype'   : arg_istype_func,
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


def handle_rules(msg, rules):
    log.info('Matching message against rules.')

    for rule in rules:
        rule_name, rule_lines = rule

        match_lines, action_lines = rule_lines
        log.debug('Matching against rule [%s]', rule_name)

        match_group = ()

        for line in match_lines:
            obj, verb = line[0:2]
            arguments = line[2:]

            f = match_rules[obj + ' ' + verb]
            res, msg, match_group = f(msg, line[2:], match_group)

            if not res:
                rule_matched = False
                break
        else:
            rule_matched = True

        if rule_matched:
            log.info('Rule [%s] matched.', rule_name)
            for line in action_lines:
                obj, verb, action = line
                log.info('\tExecuting action "%s = %s" for rule [%s].',
                         obj + ' ' + verb, action, rule_name)
                f = action_rules[obj + ' ' + verb]
                res, msg, match_group = f(msg, action, match_group)
                if not res:
                    break
            break
    else:
        log.info('No rule matched.')


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='count',
                        help='increase log verbosity level (pass multiple times)')
    parser.add_argument('msg', help='message to handle')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('kind', help='kind of message',
                       nargs='?',
                       choices=[k.name for k in Kind])
    group.add_argument('--guess',  action='store_true',
                       help='guess the kind of the message')

    parser.add_argument('--config', type=argparse.FileType('r'),
                        help='config file to use')
    parser.add_argument('--rule', type=argparse.FileType('r'),
                        help='rule file to use')

    args = parser.parse_args()

    if args.kind:
        args.kind = Kind[args.kind]

    return args


def setup_logger(verbosity):
    if verbosity:
        log_levels = {
            1 : log.WARNING,
            2 : log.INFO,
            3 : log.DEBUG
        }
        try:
            verbosity = log_levels[verbosity]
        except KeyError:
            verbosity = log.DEBUG

        log.basicConfig(format='%(levelname)s:\t%(message)s', level=verbosity)

    else:
        log.basicConfig(format='%(levelname)s:\t%(message)s')


def parse_rules(args, config):
    parser = make_parser()

    rule_file = None

    if args.rule:
        rule_file = args.rule
    else:
        default_rule = config['rules file']
        try:
            rule_file = open(default_rule)
        except OSError as e:
            log.error(str(e))
            return -1

    log.info('Using rule file {}'.format(rule_file.name))
    rules = parse_rule_file(parser, rule_file)
    rule_file.close()
    log.info('Rules parsed.')

    return rules


def parse_config(args):
    def_rule_dir = os.path.join(BaseDirectory.xdg_config_home, 'mario', \
                                'rules.d')
    def_rule_file = os.path.join(BaseDirectory.xdg_config_home, 'mario', \
                                'mario.plumb')
    defaults = {
            'strict content lookup' : False,            # TODO
            'notifications'         : False,            # TODO
            'rules file'            : def_rule_file,
            'rules dir'             : def_rule_dir,     # TODO
    }

    config = configparser.ConfigParser(defaults=defaults,
                                       default_section='mario')

    config_file = None

    if args.config:
        config_file = args.config
    else:
        default_config = os.path.join(BaseDirectory.xdg_config_home, 'mario', \
                                      'config')
        try:
            config_file = open(default_config)
        except OSError as e:
            log.info(str(e))
            return defaults

    log.info('Using config file {}'.format(config_file.name))

    config.read_file(config_file)
    config_file.close()

    log.info('Config parsed.')

    return config.defaults()


def main():
    args = parse_arguments()

    setup_logger(args.verbose)

    config = parse_config(args)

    if args.guess:
        log.info('Using heuristics to guess kind...')
        url = urlparse(args.msg)
        if url.scheme:
            args.kind = Kind.url
        else:
            args.kind = Kind.raw
        log.info('\tGuessed kind {}'.format(args.kind))

    msg = {'data' : args.msg,
           'kind' : args.kind
          }

    if args.kind == Kind.url:
        url = urlparse(args.msg)
        msg['netloc'] = url.netloc
        msg['netpath'] = url.path

    # probably a hack and possibly a reason why we can't really read in
    # messages (or rather, the data part of the message) as a command-line
    # parameter
    if args.kind == Kind.raw and type(args.msg) != bytes:
        args.msg = args.msg.encode('utf-8')

    rules = parse_rules(args, config)

    handle_rules(msg, rules)


if __name__ == '__main__':
    main()
