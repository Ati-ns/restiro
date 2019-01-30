from .docstring import DocstringDefinitionParser, DocstringResourceParser


class Parser:

    @staticmethod
    def load_from_path(base_path: str = '.'):
        """
        Load and parse files 
        
        :param base_path: 
        :return: List of resources that grouped by version
        """
        definition_parser = DocstringDefinitionParser()
        definition_parser.load_from_path(base_path)
        resource_parser = DocstringResourceParser(definition_parser.definitions)
        resource_parser.load_from_path(base_path)
        return resource_parser.export_to_model()
