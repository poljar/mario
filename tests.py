import unittest

from parser import make_parser, parse_rule_string


rule_test1 = '''[test]
arg matches {data} regex_string
plumb open firefox'''

rule_res1 = [
                ['test', (
                    [
                        ['arg', 'matches', '{data}', ['regex_string']]
                    ],
                    [
                        ['plumb', 'open', 'firefox']]
                    )
                ]
            ]


rule_test2 = '''[test]
arg matches {data} regex_string
                   regex_inbetween
plumb open firefox'''

rule_res2 = [
                ['test', (
                    [
                        ['arg', 'matches', '{data}', ['regex_string', 'regex_inbetween']]], \
                    [
                        ['plumb', 'open', 'firefox']]
                    )
                ]
            ]


rule_test3 = '''[test]
arg matches {data} regex_string
                   regex_inbetween
plumb open firefox
[test2]
arg is {data} something
plumb open echo {data}'''

rule_res3 = [
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

plumb open firefox'''


class ParserTest(unittest.TestCase):
    def test_simple_rule(self):
        parser = make_parser()
        result = parse_rule_string(parser, rule_test1)
        self.assertEqual(result, rule_res1)

    def test_multiple_match_args(self):
        parser = make_parser()
        result = parse_rule_string(parser, rule_test2)
        self.assertEqual(result, rule_res2)

    def test_multiple_rules(self):
        parser = make_parser()
        result = parse_rule_string(parser, rule_test3)
        self.assertEqual(result, rule_res3)

    def test_rule_with_comment(self):
        parser = make_parser()
        result = parse_rule_string(parser, rule_with_comment)
        self.assertEqual(result, rule_res1)

if __name__ == '__main__':
        unittest.main()
