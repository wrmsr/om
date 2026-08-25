# Copyright (c) 2010, 2013 PyMySQL contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import configparser


##


class Parser(configparser.RawConfigParser):
    def __init__(self, **kwargs):
        kwargs['allow_no_value'] = True
        configparser.RawConfigParser.__init__(self, **kwargs)

    def __remove_quotes(self, value):
        quotes = ["'", '"']
        for quote in quotes:
            if len(value) >= 2 and value[0] == value[-1] == quote:
                return value[1:-1]
        return value

    def optionxform(self, key):
        return key.lower().replace('_', '-')

    def get(self, section, option):  # type: ignore[override]
        value = configparser.RawConfigParser.get(self, section, option)
        return self.__remove_quotes(value)
