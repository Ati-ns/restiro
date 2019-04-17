import textwrap
from warnings import warn_explicit
from restiro.constants import (
    within_brackets_regex,
    within_parentheses_regex,
    single_word_regex,
    path_regex
)

from restiro.models import (
    FormParam, QueryParam, HeaderParam, URLParam, Resource
)

from restiro.exceptions import MissedParameter, InvalidDefinition

params_map = {
    'form': FormParam,
    'query': QueryParam,
    'head': HeaderParam,
    'url': URLParam
}


class DocstringApiResource:

    def __init__(self, docstring, filename, definitions: dict = None):
        self.version = None
        self.method = None
        self.path = None
        self.group = None
        self.title = None
        self.params = []
        self.permissions = []
        self.definitions = definitions
        self.description = None
        self.filename = filename
        original_docstring = docstring.group()[3:-3]
        docstring = textwrap.dedent(original_docstring).lstrip()

        prepared_lines = []
        for line in docstring.split('\n'):
            # Join lines
            if line[:1] != '@':
                prepared_lines[-1] = '%s\n%s' % (prepared_lines[-1], line)
            else:
                prepared_lines.append(line)

        for index, line in enumerate(prepared_lines):
            if line.startswith('@api '):
                if self.parse_api(line, index):
                    self.title = self.title.strip()

            elif line.startswith('@apiVersion '):
                self.parse_version(line)
                self.version = self.version.strip()

            elif line.startswith('@apiGroup '):
                self.parse_group(line)
                self.group = self.group.strip()

            elif line.startswith('@apiPermission '):
                self.parse_permission(line)

            elif line.startswith('@apiDescription '):
                self.parse_description(line)
                self.description = self.description.strip()

            elif line.startswith('@apiParam '):
                self.parse_param(line, index, 'form')

            elif line.startswith('@apiQueryParam '):
                self.parse_param(line, index, 'query')

            elif line.startswith('@apiUrlParam '):
                self.parse_param(line, index, 'url')

            elif line.startswith('@apiHeadParam '):
                self.parse_param(line, index, 'head')

            elif line.startswith('@apiUse '):
                new_lines = self.parse_use_define(line, index)
                prepared_lines.extend(new_lines)

    def parse_use_define(self, line: str, index):
        name_match, name = self._get_name(line)
        name = name.strip()
        definition_lines = []
        is_found = None
        for key, define in self.definitions.items():
            if key == name:
                definition_lines = str(define.content).split('\n')
                is_found = True
        if not is_found:
            warn_explicit('There is not such apiDefine %s' % name,
                          InvalidDefinition, self.filename, index)

        return definition_lines

    @staticmethod
    def _get_type(line: str):
        try:
            type_match = next(within_brackets_regex.finditer(line))
            type_ = type_match.group()[1:-1]
        except StopIteration:
            type_match = None
            type_ = None

        return type_match, type_

    @staticmethod
    def _get_group(line: str):
        try:
            group_match = next(within_parentheses_regex.finditer(line))
            group = group_match.group()[1:-1]
        except StopIteration:
            group_match = None
            group = None

        return group_match, group

    @staticmethod
    def _get_name(line: str):
        try:
            name_match = next(single_word_regex.finditer(line))
            name = name_match.group().strip()
        except StopIteration:
            name_match = None
            name = None

        return name_match, name

    @staticmethod
    def _get_path(line: str):
        try:
            path_match = next(path_regex.finditer(line))
            path = path_match.group().strip()
        except StopIteration:
            path_match = None
            path = None

        return path_match, path

    def parse_api(self, line: str, index: int):
        type_match, type_ = self._get_type(line)
        if type_match is None:
            warn_explicit('Missed api name',
                          MissedParameter, self.filename, index)

        path_match, path = self._get_path(line)
        if path_match is None:
            warn_explicit('Missed path name',
                          MissedParameter, self.filename, index)
            return False

        type_match_span = (-1, -1) if type_match is None else type_match.span()
        path_match_span = path_match.span()

        self.method = type_
        self.path = path
        self.title = line[max(type_match_span[1], path_match_span[1]):].strip()
        return True

    def parse_permission(self, line: str):
        permissions = line.replace('@apiPermission ', '')
        permissions = permissions.split(',')
        for permission in permissions:
            self.permissions.append(permission.strip())

    def parse_group(self, line: str):
        self.group = line.replace('@apiGroup ', '')

    def parse_version(self, line: str):
        self.version = line.replace('@apiVersion ', '')

    def parse_param(self, line: str, index: int, param_type: str):
        group_match, group = self._get_group(line)
        type_match, type_ = self._get_type(line)
        name_match, name = self._get_name(line)

        if name_match is None:
            warn_explicit('Missed api parameter `name`', MissedParameter,
                          self.filename, index)
            return False

        if name.startswith('['):
            name = name[1:-1]
            optional = True
        else:
            optional = False

        group_match_span = (-1, -1) \
            if group_match is None else group_match.span()
        type_match_span = (-1, -1) if type_match is None else type_match.span()
        name_match_span = name_match.span()
        description = line[max(type_match_span[1],
                               group_match_span[1], name_match_span[1]):]
        des_lines = description.split('\n')
        des_result = ''
        for st in des_lines:
            des_result = ' '.join((des_result, st.strip())) \
                if len(des_lines) > 1 else st.strip()

        names = name.split('=')
        default = names[1] if len(names) > 1 else None

        self.params.append({
            'name': name,
            'group': group,
            'type': type_,
            'default': default,
            'description': line[max(type_match_span[1], group_match_span[1],
                                    name_match_span[1]):],
            'optional': optional,
            'param_type': param_type
        })
        return True

    def parse_description(self, line: str):
        temp_description = line.replace('@apiDescription ', '')
        # reg = re.compile('\n(?!\s*\n)([\r\t\f\v])*')
        des = temp_description.split('\n')
        t = ''
        for s in des:
            if s not in ('', ' ', '\t', '\n'):
                t = t + s.strip() + ' '
            else:
                t = t + '\n'
        self.description = t if not self.description \
            else '\n'.join((self.description, t))

    def __repr__(self):
        return '\n'.join((
            'method: %s' % self.method,
            'path: %s' % self.path,
            'title: %s' % self.title,
            'version: %s' % self.version,
            'group: %s' % self.group,
            'description: %s' % self.description,
            'permissions: %s' % self.permissions.__repr__(),
            'params: %s' % self.params.__repr__()
        ))

    def to_model(self):

        params_in_model = list(map(
            lambda param: params_map[param['param_type']](
                name=param['name'],
                description=param['description'],
                type_=param['type'],
                required=not param['optional'],
                default=param['default']
            ),
            self.params
        ))

        return Resource(
            path=self.path,
            method=self.method,
            tags=[self.group],
            display_name=self.title,
            description=self.description,
            security={'roles': self.permissions},
            params=params_in_model
        )
