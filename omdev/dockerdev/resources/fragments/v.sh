V_TAG=$(git ls-remote --tags --refs --sort=-v:refname 'https://github.com/vlang/v' 'refs/tags/[0-9]*' | head -n1 | sed 's#.*refs/tags/##') ;

git clone --depth 1 --branch "$V_TAG" 'https://github.com/vlang/v' ~/.v ;

(cd ~/.v && make && ~/.v/v symlink ) ;
