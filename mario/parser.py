#!/usr/bin/env python3
# Copyright (c) 2015 Damir Jelić
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from pyparsing import *


def make_parser():
    ParserElement.setDefaultWhitespaceChars('')

    EOL    = LineEnd().suppress()
    Space  = Literal(' ').suppress()
    Tab    = Literal('\t').suppress()
    WS     = OneOrMore(Space) | OneOrMore(Tab)

    Comment   = LineStart() + ZeroOrMore(' ') + '#' + restOfLine + EOL | \
                OneOrMore(' ') + '#' + restOfLine
    BlankLine = LineStart() + ZeroOrMore(' ') + EOL

    alphas_extra = ''.join(chr(x) for x in range(0x100, 0x350))

    # NOTE: this are not all 'printable' Unicode characters if needed expand
    # the alphas_extra variable.
    utf8_printables = printables + alphas8bit + alphas_extra

    ArgTxt   = Word(utf8_printables)('arg')
    # TODO: allow the excluded chars if they are escaped.
    NameTxt  = Word(utf8_printables, excludeChars='{ } [ ]')

    Variable = Word(utf8_printables)

    KindObjects = Keyword('kind')
    KindVerbs   = Keyword('is')
    KindArgs    = Keyword('url')  | \
                  Keyword('raw')

    KindMatchRule = Group(KindObjects('object') + WS + \
                          KindVerbs('verb')     + WS + \
                          KindArgs('args'))

    MatchArg = Group(ArgTxt + ZeroOrMore(EOL + WS + ArgTxt))
    MatchArg = MatchArg('arg')

    MatchObjects = Keyword('arg')
    MatchVerbs   = Keyword('is')      | \
                   Keyword('istype')  | \
                   Keyword('matches') | \
                   Keyword('rewrite')
    MatchVerbs   = MatchVerbs('verb')

    ArgMatchRule = Group(Keyword('arg')('object') + WS + \
                         MatchVerbs               + WS + \
                         Variable('var')          + WS + \
                         MatchArg)
    ArgMatchRule = ArgMatchRule('match-rule')

    DataMatchRule = Group(Keyword('data')('object') + WS + \
                          MatchVerbs                + WS + \
                          MatchArg)
    DataMatchRule = DataMatchRule('match-rule')

    # Transform every 'data match' rule to an equivalent 'arg match' rule
    def data_to_arg_rule(toks):
        assert(len(toks) == 1)
        return [['arg', toks[0]['verb'], '{data}', list(toks[0]['arg'])]]

    DataMatchRule.setParseAction(data_to_arg_rule)

    MatchRule = ArgMatchRule | DataMatchRule

    MatchLines = Group(Optional(KindMatchRule('kind-rule') + EOL) + \
                       MatchRule + ZeroOrMore(EOL + MatchRule)) | \
                 Group(KindMatchRule('kind-rule'))

    ActionObject = Keyword('plumb')
    ActionVerb   = Keyword('run')     | \
                   Keyword('download')

    ActionArg = Combine(Word(utf8_printables) + \
                ZeroOrMore(OneOrMore(' ') + NotAny('#') + Word(utf8_printables)))

    ActionRule = Group(ActionObject('object') + WS + \
                       ActionVerb('verb')     + WS + \
                       ActionArg('arg'))

    ActionRule = ActionRule('act-rule')

    ActionLines = Group(ActionRule + ZeroOrMore(EOL + ActionRule))

    RuleName = Suppress('[') + NameTxt + Suppress(']') + EOL

    Rule = Group(RuleName('name') + \
                 MatchLines('match-lines') + EOL + \
                 ActionLines('act-lines'))

    RuleFile = Rule('rule') + ZeroOrMore(EOL + Rule('rule')) + \
               ZeroOrMore(EOL) + StringEnd()
    RuleFile = RuleFile('rules')

    RuleFile.ignore(Comment)
    RuleFile.ignore(BlankLine)

    return RuleFile


def extract_parse_result(result):
    rules = []

    for rule in result.asList():
        rules += [[rule[0], (rule[1], rule[2])]]

    return rules


def print_parse_error(e):
    print(e, ':\n\t', e.line)
    error_indicator = '\t' + ' ' * e.col + '^'

    print(error_indicator)


def parse_rule_file(parser, rule_file):
    try:
        result = parser.parseFile(rule_file)
    except ParseException as e:
        print_parse_error(e)
        return None

    return extract_parse_result(result)


def parse_rule_string(parser, rule_string):
    try:
        result = parser.parseString(rule_string)
    except ParseException as e:
        print_parse_error(e)
        return None

    return extract_parse_result(result)
