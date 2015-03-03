import unittest

from parser import make_parser, parse_rule_string


simple_rule = '''[test]
arg matches {data} regex_string
plumb open firefox'''

simple_res = [
                ['test', (
                    [
                        ['arg', 'matches', '{data}', ['regex_string']]
                    ],
                    [
                        ['plumb', 'open', 'firefox']]
                    )
                ]
            ]


multiple_margs_rule = '''[test]
arg matches {data} regex_string
                   regex_inbetween
plumb open firefox'''

multiple_margs_res = [
                ['test', (
                    [
                        ['arg', 'matches', '{data}', ['regex_string', 'regex_inbetween']]], \
                    [
                        ['plumb', 'open', 'firefox']]
                    )
                ]
            ]


multiple_rules = '''[test]
arg matches {data} regex_string
                   regex_inbetween
plumb open firefox
[test2]
arg is {data} something
plumb open echo {data}'''

multiple_res = [
                ['test', (
                    [
                        ['arg', 'matches', '{data}', ['regex_string', 'regex_inbetween']]
                    ],
                    [
                        ['plumb', 'open', 'firefox']
                    ]
                    )
                ], \
                ['test2', (
                    [
                        ['arg', 'is', '{data}', ['something']]
                    ],
                    [
                        ['plumb', 'open', 'echo {data}']
                    ]
                    )
                ]
            ]

rule_with_comment = '''# this is a comment
[test] # even here?
# another one
    
arg matches {data} regex_string # commenting is fun

   # maybe here with some whitespace?

plumb open firefox

#even here ?'''


class ParserTest(unittest.TestCase):
    def parser_test_helper(self, rule, result):
        parser = make_parser()
        res = parse_rule_string(parser, rule)
        self.assertEqual(result, res)

    def test_simple_rule(self):
        self.parser_test_helper(simple_rule, simple_res)

    def test_multiple_match_args(self):
        self.parser_test_helper(multiple_margs_rule, multiple_margs_res)

    def test_multiple_rules(self):
        self.parser_test_helper(multiple_rules, multiple_res)

    def test_rule_with_comment(self):
        self.parser_test_helper(rule_with_comment, simple_res)

if __name__ == '__main__':
        unittest.main()
