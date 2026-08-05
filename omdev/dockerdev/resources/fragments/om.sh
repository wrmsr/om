curl -LsSf 'https://raw.githubusercontent.com/wrmsr/om/master/omdev/cli/install.py' | bash --login -c 'python3 - $@' - \
  omcore-cext \
  omdev-cext \
  ominfra \
  omllm \
  \
  pip \
  \
  asttokens \
  executing \
  \
  orjson \
  pyyaml \
  \
  textual \
  textual-speedups \
  \
  pg8000 \
  pymysql \
;
