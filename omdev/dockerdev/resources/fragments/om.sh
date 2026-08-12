curl -LsSf 'https://raw.githubusercontent.com/wrmsr/om/master/omdev/cli/install.py' | bash --login -c 'python3 - $@' - \
  omcore-cext \
  omcore-mypyc \
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
  pg8000 \
  pymysql \
  \
  textual \
  textual-speedups \
;
