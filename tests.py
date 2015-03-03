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
    def test_simple_rule(self):
        parser = make_parser()
        result = parse_rule_string(parser, simple_rule)
        self.assertEqual(result, simple_res)

    def test_multiple_match_args(self):
        parser = make_parser()
        result = parse_rule_string(parser, multiple_margs_rule)
        self.assertEqual(result, multiple_margs_res)

    def test_multiple_rules(self):
        parser = make_parser()
        result = parse_rule_string(parser, multiple_rules)
        self.assertEqual(result, multiple_res)

    def test_rule_with_comment(self):
        parser = make_parser()
        result = parse_rule_string(parser, rule_with_comment)
        self.assertEqual(result, simple_res)

if __name__ == '__main__':
        unittest.main()
