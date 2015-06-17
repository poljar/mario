#!/usr/bin/env python3
# Copyright (c) 2015 Damir Jelić, Denis Kasak
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
    ParserElement.setDefaultWhitespaceChars(' \t')

    EOL    = OneOrMore(LineEnd()).suppress().setName("end of line")
    Spaces = OneOrMore(" ").suppress()

    # NOTE: These are not all 'printable' Unicode characters.
    # If needed, expand the alphas_extra variable.
    alphas_extra = ''.join(chr(x) for x in range(0x100, 0x350))
    chars = printables + alphas8bit + alphas_extra
    Token = Word(chars)

    InlineComment    = '#' - SkipTo(EOL)
    WholelineComment = LineStart() + '#' - restOfLine - EOL

    Argument = Token('arg').setName('argument')
    Variable = Token('var').setName('variable')

    KindObject  = Keyword('kind')('object')
    KindVerb    = Keyword('is'  )('verb')
    Kind        = Named(Keyword('url')
                       |Keyword('raw'))('arg')

    MatchObject = Named(Keyword('arg' ))('object')
    data        = Named(Keyword('data'))('object')
    MatchVerb   = Named(Keyword('is'     )
                       |Keyword('istype' )
                       |Keyword('matches')
                       |Keyword('rewrite'))('verb').setName('verb')
    Pattern     = Named(Group(OneOrMore(Spaces + Argument + EOL)))('arg').leaveWhitespace()

    ActionObject = Keyword('plumb')('object')
    ActionVerb   = Named(Keyword('run'     )
                        |Keyword('download'))('verb')
    Action       = Named(originalTextFor(OneOrMore(Argument)))('arg')

    ArgMatchClause  = Group(MatchObject - MatchVerb - Variable - Pattern)
    DataMatchClause = Group(data - MatchVerb - Pattern)

    # Transform every 'data match' rule to an equivalent 'arg match' rule
    def data_to_arg(toks):
        assert(len(toks) == 1)
        toks[0][0] = 'arg'
        toks[0].insert(2, '{data}')
        return toks

    DataMatchClause.setParseAction(data_to_arg)

    KindClause   = Group(KindObject - KindVerb - Kind) - EOL
    MatchClause  = (DataMatchClause | ArgMatchClause)
    ActionClause = Group(ActionObject - ActionVerb - Action) - EOL

    MatchBlock  = Group(ZeroOrMore(MatchClause('match-clause')))
    ActionBlock = Group(OneOrMore(ActionClause('action-clause')))

    # TODO: allow the excluded chars if they are escaped.
    RuleName = Word(chars, excludeChars='{ } [ ]')('rule-name')
    RuleHeading = Suppress('[') - RuleName - Suppress(']') - EOL
    Rule = Group(RuleHeading
                - KindClause('kind-clause')
                - MatchBlock('match-block')
                - ActionBlock('action-block'))
    RulesFile = OneOrMore(Rule)
    RulesFile.ignore(WholelineComment)
    RulesFile.ignore(InlineComment)

    for v in [MatchObject, ActionObject]:
        v.setName('object')

    for v in [MatchVerb, ActionVerb]:
        v.setName('verb')

    Kind.setName('kind')
    data.setName('object')
    Pattern.setName('pattern')
    Action.setName('action or url')
    KindClause.setName('kind clause')
    MatchClause.setName('match clause')
    ActionClause.setName('action clause')
    MatchBlock.setName('match block')
    ActionBlock.setName('action block')
    Rule.setName('rule')
    RuleName.setName('rule name')
    RulesFile.setName('rules')

    return RulesFile


def extract_parse_result(result):
    rules = []

    for rule in result:
        rules += [[rule['rule-name'],
                    (rule['kind-clause'] + rule['match-block'],
                     rule['action-block'])
                 ]]

    return rules


def extract_parse_result_as_list(result):
    rules = []

    for rule in result.asList():
        rules += [[rule[0], (rule[1], rule[2], rule[3])]]

    return rules


def print_parse_error(e):
    print(e, ':\n\t', e.line, sep="")
    error_indicator = '\t' + ' ' * (e.col - 1) + '^'

    print(error_indicator)


def catch_parse_errors(f, handler=print_parse_error):
    @wraps(f)
    def w(x, *args):
        try:
            return f(x, *args)
        except (ParseException, ParseSyntaxException) as e:
            handler(e)

    return w


def parse_rules_file_exc(parser, rules_file,
        extract_function=extract_parse_result):
    s = rules_file.read().rstrip()
    result = parser.parseString(s, parseAll=True)

    return extract_function(result)


def parse_rules_string_exc(parser, rule_string,
        extract_function=extract_parse_result):
    result = parser.parseString(rule_string, parseAll=True)

    return extract_function(result)


parse_rules_file = catch_parse_errors(parse_rules_file_exc)
parse_rules_string = catch_parse_errors(parse_rules_string_exc)
