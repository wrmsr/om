# Copyright (c) 2010-2016 PyMySQL contributors
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
"""
TODO:
 - https://github.com/PyMySQL/PyMySQL/commit/0305ab344f2026aaa17b405684a521b092a650bd
 - https://github.com/PyMySQL/PyMySQL/commit/10739bc7781fb85bb9df3d21c2465ba9c3988a2c
"""
from .... import dataclasses as _dc


_dc.init_package(
    globals(),
    codegen=True,
)


##


from .... import lang as _lang  # noqa


with _lang.auto_proxy_init(globals()):
    ##

    from .core.asyncio import (   # noqa
        AsyncioConnection,
    )

    from .core.base import (  # noqa
        BaseConnection,
    )

    from .core.sync import (  # noqa
        SyncConnection,
    )

    from .cursors.formatting import (  # noqa
        mogrify,
    )

    from .protocol.messages import (  # noqa
        ColumnDefinition,
    )

    from .protocol.session import (  # noqa
        QueryResult,
        UnbufferedResult,
    )
