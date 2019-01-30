import unittest

from os.path import join

from webtest_docgen import Parser
from webtest_docgen.tests.helpers import WebAppTestCase

from pprint import pprint


class ParserTestCase(WebAppTestCase):

    def test_parser(self):
        online_store_path = join(self.stuff_path, 'online_store')
        resources_by_version = Parser.load_from_path(online_store_path)

        for y, x in resources_by_version['1.0.0'].items():
            pprint(x.to_dict())


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
