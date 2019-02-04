import unittest

from os.path import join

from webtest_docgen import (
    Parser,
    Resources,
    Resource,
    QueryParam,
    URLParam
)
from webtest_docgen.parser.docstring import (
    DocstringResourceParser,
    DocstringDefinitionParser
)
from webtest_docgen.tests.helpers import WebAppTestCase

from pprint import pprint


class ParserTestCase(WebAppTestCase):

    def test_parser(self):
        online_store_path = join(self.stuff_path, 'online_store')
        wrong_usecases_path = join(self.stuff_path, 'wrong_usecases')

        resources_by_version = Parser.load_from_path(online_store_path)

        for y, x in resources_by_version['1.0.0'].items():
            pprint(x.to_dict())

        example_resource = [
            Resource(
                path='/product',
                method='get',
                display_name='Get all products',
                tags=['Product'],
                params=[
                    QueryParam(
                        name='sort',
                        type_=None,
                        required=False
                    )
                ],
                security={'roles': ['god', 'operator']}
            ),
            Resource(
                path='/product/:productId',
                method='get',
                display_name='Get a seller',
                params=[
                    URLParam(
                        name='productId',
                        required=True,
                        type_='Integer')
                ]
            )
        ]

        # Key of resource in Resources 'path-method'
        self.assertIsInstance(resources_by_version['1.0.0'], Resources)
        resource = resources_by_version['1.0.0']['/product-get']

        self.assertEqual(resource.method, example_resource[0].method)
        self.assertEqual(resource.path, example_resource[0].path)
        self.assertEqual(resource.display_name,
                         example_resource[0].display_name)
        self.assertEqual(resource.tags[0], example_resource[0].tags[0])
        self.assertEqual(resource.security, example_resource[0].security)
        self.assertEqual(len(resource.params), 4)
        self.assertIsInstance(resource.params[0], QueryParam)
        self.assertEqual(resource.params[0].name,
                         example_resource[0].params[0].name)
        self.assertEqual(resource.params[0].type_,
                         example_resource[0].params[0].type_)
        self.assertEqual(resource.params[0].required,
                         example_resource[0].params[0].required)

        # test represent of a resource
        result_rep = resource.__repr__()
        self.assertIsInstance(result_rep, str)
        print(result_rep, '@@@')

        definition_parser = DocstringDefinitionParser()
        definition_parser.load_from_path(online_store_path)
        doc_parser = DocstringResourceParser(definition_parser.definitions)

        # An api without name
        with self.assertRaises(Exception):
            doc_parser.load_file(join(wrong_usecases_path, 'wrong_api_name.py'))

        # api without path
        with self.assertRaises(Exception):
            doc_parser.load_file(join(wrong_usecases_path, 'wrong_api_path.py'))

        # no name parameter
        with self.assertRaises(Exception):
            doc_parser.load_file(
                join(wrong_usecases_path, 'missed_parameter_name.py'))

        # use of not define block
        with self.assertRaises(Exception):
            doc_parser.load_file(join(wrong_usecases_path, 'wrong_api_use.py'))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
