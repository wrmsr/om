sudo curl -fsSL 'https://apt.llvm.org/llvm-snapshot.gpg.key' -o /etc/apt/keyrings/apt.llvm.org.asc ;
sudo chmod 0644 /etc/apt/keyrings/apt.llvm.org.asc ;

{
  echo 'Types: deb' ;
  echo 'URIs: https://apt.llvm.org/noble/' ;
  printf 'Suites:' ;
  for v in $LLVM_VERSIONS; do \
    printf ' llvm-toolchain-noble-%s' "$v" ;
  done ;
  printf '\n' ;
  echo 'Components: main' ;
  echo 'Signed-By: /etc/apt/keyrings/apt.llvm.org.asc' ;
} | sudo tee /etc/apt/sources.list.d/llvm.sources > /dev/null ;

sudo apt-get update ;

for v in $LLVM_VERSIONS ; do \
  sudo apt-get install -y --no-install-recommends \
    "llvm-$v" \
    "llvm-$v-dev" \
    "clang-$v" \
    "lld-$v" ;
done ;
