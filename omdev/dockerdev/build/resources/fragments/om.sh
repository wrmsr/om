curl -LsSf 'https://raw.githubusercontent.com/wrmsr/om/master/omdev/cli/install.py' | bash --login -c 'python3 - $@' - \
  --ft \
  \
  'omcore[cext,mypyc,plus]' \
  'omdev[cext]' \
  'ominfra' \
  'omllm' \
  \
  'pip' \
;

bash --login -c 'om $@' - cli python -m omdev.imports.pycz \
  omcore \
  omdev \
  ominfra \
  omllm \
;
