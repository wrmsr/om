curl -LsSf 'https://raw.githubusercontent.com/wrmsr/om/master/omdev/cli/install.py' | bash --login -c 'python3 - $@' - \
  'omcore[cext,mypyc,plus]' \
  omdev-cext \
  ominfra \
  omllm \
  \
  pip \
  \
  textual \
  textual-speedups \
;
