# Overview

Infrastructure and cloud code.

# Notable packages

- **[clouds.aws](https://github.com/wrmsr/om/blob/master/ominfra/clouds/aws)** - boto-less aws tools, including
  authentication and generated service dataclasses.

- **[journald2aws](https://github.com/wrmsr/om/blob/master/ominfra/clouds/aws/journald2aws)**
  ([amalg](https://github.com/wrmsr/om/blob/master/ominfra/scripts/journald2aws.py)) - a self-contained little tool that
  forwards journald to cloudwatch.
