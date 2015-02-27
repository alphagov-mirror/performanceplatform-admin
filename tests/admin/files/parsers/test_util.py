from admin.files.parsers import ParseError
from admin.files.parsers.util import make_dicts

import unittest

from hamcrest import only_contains, assert_that


class TestMakeRecords(unittest.TestCase):

    def test_make_records_from_rows(self):
        rows = [
            ["name", "size"],
            ["bottle", 123],
            ["screen", 567],
            ["mug", 12],
        ]

        records = make_dicts(rows)

        assert_that(records, only_contains(
            {"name": "bottle", "size": 123},
            {"name": "screen", "size": 567},
            {"name": "mug", "size": 12},
        ))

    def test_fail_if_a_row_contains_more_values_than_the_first_row(self):
        rows = [
            ["name", "size"],
            ["bottle", 123],
            ["screen", 567, 8],
        ]

        self.assertRaises(ParseError,
                          lambda rows: list(make_dicts(rows)),
                          rows)

    def test_fail_if_a_row_contains_fewer_values_than_the_first_row(self):
        rows = [
            ["name", "size"],
            ["bottle", 123],
            ["screen"],
        ]

        self.assertRaises(ParseError,
                          lambda rows: list(make_dicts(rows)),
                          rows)

    def test_works_if_given_an_iterator(self):
        def rows():
            yield ("name", "size")
            yield ("bottle", 123)
            yield ("screen", 567)

        records = list(make_dicts(rows()))

        assert_that(records, only_contains(
            {"name": "bottle", "size": 123},
            {"name": "screen", "size": 567},
        ))

    def test_ignores_empty_rows(self):
        rows = [
            ["name", "size"],
            ["val1", 123],
            ["", ""],
            [None, None],
            ["val2", 456]
        ]

        records = list(make_dicts(rows))

        assert_that(records, only_contains(
            {"name": "val1", "size": 123},
            {"name": "val2", "size": 456},
        ))

    def test_processes_rows_containg_just_numbers_correctly(self):
        rows = [
            ['count'],
            [818],
            [602],
        ]

        records = list(make_dicts(rows))

        assert_that(records, only_contains(
            {'count': 818},
            {'count': 602},
        ))
