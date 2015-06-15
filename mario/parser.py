#!/usr/bin/env python3
# Copyright (c) 2015 Damir Jelić
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from pyparsing import *
from functools import wraps

class Named(ParseElementEnhance):
    def parseImpl(self, instring, loc, doActions = True):
        try:
            return super(Named,self).parseImpl(instring, loc, doActions)
        except ParseBaseException as pbe:
            pbe.msg = "Expected " + str(self)
            pbe.loc = loc
            raise pbe

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
    KindArgs    = Keyword('url') | Keyword('raw')

    KindMatchRule = Group(KindObjects('object') + WS +
                          KindVerbs('verb')     + WS +
                          KindArgs('args'))

    MatchArg = Group(ArgTxt + ZeroOrMore(EOL + WS + ArgTxt))
    MatchArg = MatchArg('arg')

    MatchObjects = Keyword('arg')
    MatchVerbs   = (Keyword('is')      |
                    Keyword('istype')  |
                    Keyword('matches') |
                    Keyword('rewrite'))
    MatchVerbs   = MatchVerbs('verb')

    ArgMatchRule = Group(Keyword('arg')('object') + WS +
                         MatchVerbs               + WS +
                         Variable('var')          + WS +
                         MatchArg)
    ArgMatchRule = ArgMatchRule('match-rule')

    DataMatchRule = Group(Keyword('data')('object') + WS +
                          MatchVerbs                + WS +
                          MatchArg)
    DataMatchRule = DataMatchRule('match-rule')

    # Transform every 'data match' rule to an equivalent 'arg match' rule
    def data_to_arg_rule(toks):
        assert(len(toks) == 1)
        return [['arg', toks[0]['verb'], '{data}', list(toks[0]['arg'])]]

    DataMatchRule.setParseAction(data_to_arg_rule)

    MatchRule = ArgMatchRule | DataMatchRule

    MatchLines = (Group(Optional(KindMatchRule('kind-rule') + EOL) +
                        MatchRule + ZeroOrMore(EOL + MatchRule))   |
                  Group(KindMatchRule('kind-rule')))

    ActionObject = Keyword('plumb')
    ActionVerb   = Keyword('run') | Keyword('download')

    ActionArg = Combine(Word(utf8_printables) +
                ZeroOrMore(OneOrMore(' ') + NotAny('#') + Word(utf8_printables)))

    ActionRule = Group(ActionObject('object') + WS +
                       ActionVerb('verb')     + WS +
                       ActionArg('arg'))

    ActionRule = ActionRule('act-rule')

    ActionLines = Group(ActionRule + ZeroOrMore(EOL + ActionRule))

    RuleName = Suppress('[') + NameTxt + Suppress(']') + EOL

    Rule = Group(RuleName('name') +
                 MatchLines('match-lines') + EOL +
                 ActionLines('act-lines'))

def extract_parse_result(result):
    rules = []

    for rule in result:
        rules += [[rule['rule-name'],
                    (kind_clause + rule['match-block'],
                     rule['action-block'])
                 ]]

    return rules


def extract_parse_result_as_list(result):
    rules = []

    for rule in result.asList():
        rules += [[rule[0], (rule[1], rule[2])]]

    return rules


def print_parse_error(e):
    print(e, ':\n\t', e.line, sep="")
    error_indicator = '\t' + ' ' * e.col + '^'

    print(error_indicator)


def parse_rules_file(parser, rules_file, extract_function=extract_parse_result):
    result = parser.parseFile(rules_file)

    return extract_function(result)


def parse_rule_string(parser, rule_string, extract_function=extract_parse_result):
    result = parser.parseString(rule_string)

    return extract_function(result)
