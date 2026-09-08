# Overview

Infrastructure and cloud code.

# Notable packages

- **[clouds.aws](https://github.com/wrmsr/om/blob/master/ominfra/clouds/aws)** - boto-less aws tools, including
  authentication and generated service dataclasses.

- **[journald2aws](https://github.com/wrmsr/om/blob/master/ominfra/clouds/aws/journald2aws)**
  ([amalg](https://github.com/wrmsr/om/blob/master/ominfra/scripts/journald2aws.py)) - a self-contained little tool that
  forwards journald to cloudwatch.

- **[manage](https://github.com/wrmsr/om/blob/master/ominfra/manage)**
  ([amalg](https://github.com/wrmsr/om/blob/master/ominfra/scripts/manage.py)) - a remote system management tool,
  including a code deployment system. inspired by things like [mitogen](https://mitogen.networkgenomics.com/),
  [pyinfra](https://github.com/pyinfra-dev/pyinfra), [piku](https://github.com/piku/piku). uses
  [pyremote](https://github.com/wrmsr/om/blob/master/omcore/os/pyremote.py).
