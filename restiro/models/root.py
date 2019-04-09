from typing import List, Union
from urllib.parse import urlparse
from os import scandir

from restiro.helpers import get_examples_dir
from .resource import Resource, Resources
from .document import Document, Documents
from .translation_mixin import TranslationMixin


class DocumentationRoot(TranslationMixin):
    __translation_keys__ = (
        'title',
    )

    def __init__(self, title: str, base_uri: str = None, locale: str=None,
                 resources: Union[Resource, List[Resource]] = None,
                 documents: Union[Document, List[Document]] = None):
        """
        Documentation root class 
        :param title: The ``title`` property is a short plain text description of the RESTful API.
                      The ``title`` property's value SHOULD be suitable for use as a title for
                      the contained user documentation.

        :param base_uri: A RESTful API's resources are defined relative to the API's base URI.
                         The use of the ``base_uri`` field is OPTIONAL to allow describing APIs that
                         have not yet been implemented.
                         After the API is implemented (even a mock implementation) and can be accessed
                         at a service endpoint, the API definition MUST contain a ``base_uri`` property. 
                         The ``base_uri`` property's value MUST conform to the URI specification [RFC2396] 
                         or a Level 1 Template URI as defined in RFC 6570 [RFC6570].
                         The ``base_uri`` property SHOULD only be used as a reference value. 

        :param resources: List of the resources.
        :param documents: List of additional documentations.
        """
        self.title = title
        self.locale = locale
        self.base_uri = base_uri
        self.documents = Documents()
        self.resources = Resources()

        if documents:
            if isinstance(documents, list):
                self.set_documents(*documents)
            else:
                self.set_documents(documents)

        if resources:
            if isinstance(resources, Resources):
                self.resources = resources
            elif isinstance(resources, list):
                self.set_resources(*resources)
            else:
                self.set_resources(resources)

    def set_resources(self, *args):
        for item in args:
            self.resources.append(item)
        return self

    def set_documents(self, *args):
        for item in args:
            self.documents.append(item)
        return self

    @property
    def base_uri_path(self):
        return urlparse(self.base_uri).path if self.base_uri else ''

    def to_dict(self):
        return {
            'title': self.title,
            'locale': self.locale,
            'base_uri': self.base_uri,
            'documents': self.documents.to_dict(),
            'resources': self.resources.to_dict(),
        }

    def extract_translations(self):
        result = super().extract_translations()
        result.extend(self.documents.extract_translations())
        result.extend(self.resources.extract_translations())
        return result

    def translate(self, translator):
        super().translate(translator)
        self.documents.translate(translator)
        self.resources.translate(translator)

    def translate_all(self, locales_dir, locale, domain: str='restiro'):
        import gettext
        import locale as lib_locale

        translation = gettext.translation(
            domain=domain,
            localedir=locales_dir,
            languages=[locale]
        )
        try:
            lib_locale.setlocale(lib_locale.LC_ALL, locale)
        except lib_locale.Error:
            print('Invalid locale %s' % locale)
            raise

        self.translate(translation .gettext)

    def load_resource_examples(self, examples_dir: str=None):
        """
        Load example objects into resources

        :param examples_dir:
        :return:
        """
        from . import ResourceExample
        if not examples_dir:
            examples_dir = get_examples_dir()

        for dir_entry in scandir(examples_dir):
            pickle_filename = dir_entry.path
            resource_example = ResourceExample.load(pickle_filename)

            resource_path = resource_example.request.path
            resource_method = resource_example.request.method

            resource = self.resources.find(
                path=resource_path,
                method=resource_method
            )

            if not resource:
                resource_path = resource_path[len(self.base_uri_path):]

                resource = self.resources.find(
                    path=resource_path,
                    method=resource_method
                )

            if not resource:
                continue

            resource.examples.append(resource_example)
