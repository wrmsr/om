FROM ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55


## locale

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_COLLATE=C


## deps

RUN \
  --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
  --mount=target=/var/cache/apt,type=cache,sharing=locked \
( \
set -ex ;\
umask 0002 ;\
\
rm -f /etc/apt/apt.conf.d/docker-clean ;\
rm -f /etc/dpkg/dpkg.cfg.d/excludes ;\
\
export DEBIAN_FRONTEND=noninteractive ;\
apt-get update ;\
\
apt-get install -y locales ;\
locale-gen en_US.UTF-8 ;\
\
apt-get upgrade -y ;\
\
if [ "$(dpkg-divert --truename /usr/bin/man)" = '/usr/bin/man.REAL' ]; then\
  rm -f /usr/bin/man ;\
  dpkg-divert --quiet --remove --rename /usr/bin/man ;\
fi ;\
\
apt-get install -y --reinstall $(dpkg-query -W -f='${binary:Package} ${db:Status-Status}\n' | awk '$2=="installed"{print $1}') ;\
\
apt-get install -y man-db manpages manpages-dev ;\
rm -f /etc/update-motd.d/60-unminimize ;\
\
apt-get install -y apt-utils ;\
\
DEPS="" ;\
\
# system\
\
DEPS="$DEPS\
  apt-transport-https\
  aria2\
  autoconf\
  bindfs\
  binutils-aarch64-linux-gnu\
  binutils-multiarch\
  binutils-riscv64-linux-gnu\
  binutils-x86-64-linux-gnu\
  bison\
  bmon\
  btop\
  bubblewrap\
  build-essential\
  ca-certificates\
  capstone-tool\
  clang\
  cmake\
  curl\
  cvs\
  dnsutils\
  dumb-init\
  emacs\
  fd-find\
  ffmpeg\
  file\
  flex\
  g++\
  g++-14\
  gcc\
  gcc-14\
  gdb\
  gdb-multiarch\
  git\
  gnupg\
  gnupg-agent\
  gosu\
  graphviz\
  htop\
  imagemagick\
  iputils-ping\
  iputils-tracepath\
  irssi\
  jq\
  less\
  libavcodec-dev\
  libavformat-dev\
  libavutil-dev\
  libbz2-dev\
  libdb-dev\
  libdebuginfod-dev\
  libgdbm6\
  liblz4-dev\
  libmagick++-dev\
  libncurses5-dev\
  libpq-dev\
  libpsl-dev\
  libreadline6-dev\
  libsqlite3-dev\
  libssl-dev\
  libswscale-dev\
  libxml2-dev\
  libxslt-dev\
  libyaml-dev\
  libzstd-dev\
  lld\
  llvm\
  lsb-release\
  lsof\
  lz4\
  lzma\
  lzma-dev\
  make\
  man-db\
  maven\
  mercurial\
  moreutils\
  mosh\
  mysql-server\
  nano\
  nasm\
  ncdu\
  net-tools\
  netcat-openbsd\
  nginx\
  opensbi\
  openssh-server\
  ovmf\
  perl\
  pkg-config\
  postgresql\
  postgresql-client\
  protobuf-compiler\
  qemu-efi-aarch64\
  qemu-efi-riscv64\
  qemu-system-arm\
  qemu-system-misc\
  qemu-system-x86\
  qemu-user\
  qemu-utils\
  redis\
  ripgrep\
  ruby\
  runsc\
  silversearcher-ag\
  socat\
  software-properties-common\
  sqlite3\
  strace\
  subversion\
  sudo\
  tcpdump\
  tcsh\
  telnet\
  tesseract-ocr\
  tmux\
  u-boot-qemu\
  unzip\
  vim\
  wget\
  xsltproc\
  zip\
  zsh\
  zstd\
" ;\
\
# python\
\
DEPS="$DEPS\
  build-essential\
  gdb\
  lcov\
  libbz2-dev\
  libexpat1-dev\
  libffi-dev\
  libgdbm-compat-dev\
  libgdbm-dev\
  liblzma-dev\
  libncurses5-dev\
  libnsl-dev\
  libreadline-dev\
  libreadline6-dev\
  libsqlite3-dev\
  libssl-dev\
  libzstd-dev\
  lzma\
  lzma-dev\
  pkg-config\
  tk-dev\
  uuid-dev\
  xz-utils\
  zlib1g-dev\
" ;\
\
# x11\
\
DEPS="$DEPS\
  dbus-x11\
  x11-apps\
" ;\
\
apt-get install -y $DEPS ;\
)


## user

RUN (\
export NEW_USER='om' ;\
export NEW_UID='4317' ;\
export NEW_GID='4317' ;\
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
if id -u ubuntu >/dev/null 2>&1; then\
    userdel ubuntu ;\
fi ;\
if getent group ubuntu >/dev/null 2>&1; then\
    groupdel ubuntu ;\
fi ;\
rm -rf /home/ubuntu ;\
\
groupadd --gid ${NEW_GID} ${NEW_USER} ;\
useradd --uid ${NEW_UID} --gid ${NEW_GID} -m -s /bin/bash -d /${NEW_USER} ${NEW_USER} ;\
\
echo "${NEW_USER} ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/${NEW_USER} ;\
\
chmod 0440 /etc/sudoers.d/${NEW_USER} ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)

USER om


## firefox

RUN \
  --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
  --mount=target=/var/cache/apt,type=cache,sharing=locked \
( \
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
sudo mkdir -p /etc/apt/keyrings ;\
\
curl -fsSL \
  'https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x738BEB9321D1AAEC13EA9391AEBDF4819BE21867' |\
  sudo tee /etc/apt/keyrings/mozillateam.asc >/dev/null ;\
\
echo "\
Types: deb\n\
URIs: https://ppa.launchpadcontent.net/mozillateam/ppa/ubuntu/\n\
Suites: noble\n\
Components: main\n\
Signed-By: /etc/apt/keyrings/mozillateam.asc\n\
" | sudo tee /etc/apt/sources.list.d/mozillateam.sources >/dev/null ;\
\
echo "\
Package: *\n\
Pin: release o=LP-PPA-mozillateam\n\
Pin-Priority: 1001\n\
\n\
Package: firefox\n\
Pin: version 1:1snap1-0ubuntu2\n\
Pin-Priority: -1\n\
" | sudo tee /etc/apt/preferences.d/mozilla-firefox ;\
\
sudo apt-get update ;\
sudo apt-get install -y firefox ;\
\
echo 'Unattended-Upgrade::Allowed-Origins:: "LP-PPA-mozillateam:${distro_codename}";' |\
  sudo tee /etc/apt/apt.conf.d/51unattended-upgrades-firefox ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## cuda

RUN \
  --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
  --mount=target=/var/cache/apt,type=cache,sharing=locked \
( \
export CUDA_VERSION='13.4' ;\
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
case "$(dpkg --print-architecture)" in \
    amd64) CUDA_REPO_ARCH=x86_64 ;; \
    arm64) CUDA_REPO_ARCH=sbsa ;; \
    *) echo "Unsupported CUDA architecture: $(dpkg --print-architecture)" >&2 ; exit 1 ;; \
esac ;\
\
curl -fsSLo /tmp/cuda-keyring.deb \
    "https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/${CUDA_REPO_ARCH}/cuda-keyring_1.1-1_all.deb" ;\
sudo dpkg -i /tmp/cuda-keyring.deb ;\
rm /tmp/cuda-keyring.deb ;\
\
sudo apt-get update ;\
sudo apt-get install -y --no-install-recommends \
    "cuda-toolkit-$(echo ${CUDA_VERSION} | tr . -)" \
;\
\
echo '\n\
export CUDA_HOME="/usr/local/cuda"\n\
export PATH="$CUDA_HOME/bin:$PATH"\n\
export LD_LIBRARY_PATH="/usr/local/nvidia/lib:/usr/local/nvidia/lib64:$CUDA_HOME/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"\n\
export LIBRARY_PATH="$CUDA_HOME/lib64/stubs${LIBRARY_PATH:+:$LIBRARY_PATH}"\n\
' >> ~/.bashrc ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## cmake

RUN \
  --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
  --mount=target=/var/cache/apt,type=cache,sharing=locked \
( \
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
sudo apt install -y ca-certificates gpg wget ;\
\
test -f /usr/share/doc/kitware-archive-keyring/copyright || \
  wget -O - 'https://apt.kitware.com/keys/kitware-archive-latest.asc' 2>/dev/null | \
  gpg --dearmor - | \
  sudo tee /usr/share/keyrings/kitware-archive-keyring.gpg >/dev/null ;\
\
echo 'deb [signed-by=/usr/share/keyrings/kitware-archive-keyring.gpg] https://apt.kitware.com/ubuntu/ noble main' | \
  sudo tee /etc/apt/sources.list.d/kitware.list >/dev/null ;\
\
sudo apt update ;\
sudo apt install -y kitware-archive-keyring ;\
\
sudo apt update ;\
sudo apt install -y cmake ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## docker

RUN \
  --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
  --mount=target=/var/cache/apt,type=cache,sharing=locked \
( \
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
mkdir -p /etc/apt/keyrings ;\
curl -fsSL 'https://download.docker.com/linux/ubuntu/gpg' | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg ;\
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu\
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null ;\
\
sudo apt-get update ;\
sudo apt-get install -y docker-ce-cli ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## jdk

RUN \
  --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
  --mount=target=/var/cache/apt,type=cache,sharing=locked \
( \
export JDKS='zulu21-ca-jdk zulu25-ca-jdk zulu26-ca-jdk zulu27-ca-jdk' ;\
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
sudo apt install -y gnupg ca-certificates curl ;\
curl -s 'https://repos.azul.com/azul-repo.key' | sudo gpg --dearmor -o /usr/share/keyrings/azul.gpg ;\
echo "deb [signed-by=/usr/share/keyrings/azul.gpg] https://repos.azul.com/zulu/deb stable main" | sudo tee /etc/apt/sources.list.d/zulu.list ;\
\
sudo apt-get update ;\
sudo apt-get install -y ${JDKS} ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## deadsnakes

RUN (\
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
sudo add-apt-repository ppa:deadsnakes/ppa &&\
sudo apt update ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## rust

RUN (\
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
curl --proto '=https' --tlsv1.2 -sSf 'https://sh.rustup.rs' | sh -s -- -y ;\
\
$HOME/.cargo/bin/cargo install \
\
  cargo-edit \
  rust-script \
\
  ocrs-cli \
\
;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## go

RUN (\
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
GO_VERSION=$(curl -fsSL 'https://go.dev/VERSION?m=text' | head -n1 | sed 's/^go//') ;\
\
curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-$(dpkg --print-architecture).tar.gz" | tar -C "$HOME" -xzf - ;\
mv "$HOME/go" "$HOME/.go" ;\
\
echo '\n\
export GOROOT="$HOME/.go"\n\
export PATH="$GOROOT/bin:$PATH"\n\
' >> ~/.bashrc ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## zig

RUN (\
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
ZIG_VERSION=$(\
  curl -fsSL 'https://ziglang.org/download/index.json' |\
  jq -r 'to_entries | map(select(.key != "master")) | map(.value) | sort_by(.version) | last | .version'\
) ;\
\
curl -fsSL "https://ziglang.org/download/${ZIG_VERSION}/zig-$(uname -m)-linux-${ZIG_VERSION}.tar.xz" | tar -xJ -C "$HOME" ;\
\
mv "$HOME/zig-$(uname -m)-linux-${ZIG_VERSION}" "$HOME/.zig" ;\
\
echo '\n\
export PATH="$HOME/.zig:$PATH"\n\
' >> ~/.bashrc ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## vcpkg

RUN (\
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
git clone 'https://github.com/microsoft/vcpkg' ~/.vcpkg_root ;\
(cd ~/.vcpkg_root && ./bootstrap-vcpkg.sh) ;\
\
echo '\n\
export VCPKG_ROOT="$HOME/.vcpkg_root"\n\
' >> ~/.bashrc ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## nvm

RUN (\
export NVM_VERSIONS='20 22 24 26' ;\
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
NVM_VERSION=$(\
  curl -fsSL -o /dev/null -w '%{url_effective}' 'https://github.com/nvm-sh/nvm/releases/latest' |\
  sed 's#.*\/tag/##'\
) ;\
\
curl -o- "https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_VERSION}/install.sh" | bash ;\
\
export NVM_DIR="$HOME/.nvm" ;\
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" ;\
\
for NV in ${NVM_VERSIONS} ; do\
  nvm install "$NV" ;\
done ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## rbenv

RUN (\
export RBENV_VERSIONS='3.4 4.0' ;\
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
curl -fsSL 'https://rbenv.org/install.sh' | bash ;\
\
for RV in ${RBENV_VERSIONS}; do\
  bash -c 'eval "$(~/.rbenv/bin/rbenv init - --no-rehash bash)" && rbenv install -L | grep -F "$1." | grep -E "^[0-9]+\.[0-9]+\.[0-9]+$" | sort -V | tail -n1 | xargs rbenv install' bash "$RV" ;\
done ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## uv

RUN (\
export UV_PYTHON_VERSIONS='3.8 3.9 3.10 3.11 3.12 3.13 3.14 3.14+freethreaded 3.15 3.15+freethreaded' ;\
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
curl -LsSf 'https://astral.sh/uv/install.sh' | sh ;\
\
for PV in ${UV_PYTHON_VERSIONS} ; do\
  bash --login -c "uv python install $PV" ;\
done ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## pyenv

RUN \
  --mount=target=/om/.pyenv_cache,type=cache,sharing=locked,uid=4317,gid=4317 \
( \
export PYENV_VERSIONS='3.8.20 3.13.16 3.14.8 3.14.8t 3.15.0rc3 3.15.0rc3t' ;\
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
git clone 'https://github.com/pyenv/pyenv' ~/.pyenv ;\
\
for V in ${PYENV_VERSIONS} ; do\
  PYTHON_BUILD_CACHE_PATH=~/.pyenv_cache ~/.pyenv/bin/pyenv install -s "$V" ;\
done ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## om

RUN (\
export CHGRP_ROOTS='/om' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
curl -LsSf 'https://raw.githubusercontent.com/wrmsr/om/master/omdev/cli/install.py' | bash --login -c 'python3 - $@' - \
  --ft \
  \
  'omcore[cext,mypyc,plus]' \
  'omdev[cext]' \
  'ominfra' \
  'omllm' \
  \
  'pip' \
;\
\
bash --login -c 'om $@' - cli python -m omdev.imports.pycz \
  omcore \
  omdev \
  ominfra \
  omllm \
;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)


## sshd

RUN (\
set -ex ;\
umask 0002 ;\
\
sudo sed -i 's/^#*PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config ;\
sudo sed -i 's/^#X11UseLocalhost yes/X11UseLocalhost no/' /etc/ssh/sshd_config ;\
sudo sed -i 's/^# Ciphers and keying/Ciphers chacha20-poly1305@openssh.com/' /etc/ssh/sshd_config ;\
sudo sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd ;\
sudo mkdir /var/run/sshd ;\
)


## configs

RUN cat > /om/.gdbinit <<'EOF' && chmod 664 /om/.gdbinit
handle SIGUSR1 nostop noprint
handle SIGUSR2 nostop noprint
EOF


RUN cat > /om/.sqliterc <<'EOF' && chmod 664 /om/.sqliterc
.headers on
.mode line
.timer on
.changes on
EOF


RUN cat > /om/.tmux.conf <<'EOF' && chmod 664 /om/.tmux.conf
setw -g mode-keys vi
set -g status-keys vi
set -sg escape-time 0
set -g status-fg black
set -g history-limit 50000
set -g update-environment "DISPLAY"
set -sg default-terminal "xterm-256color"
set -g extended-keys on
EOF


RUN cat > /om/.vimrc <<'EOF' && chmod 664 /om/.vimrc
set number
syntax on
filetype indent plugin on
set tabstop=4
set shiftwidth=4
set expandtab
EOF



## scripts

RUN (\
mkdir /om/scripts && chmod -R g=u /om/scripts ;\
)

RUN cat > /om/scripts/install-claude <<'EOF' && chmod 664 /om/scripts/install-claude
#!/bin/bash
set -e

command -v claude >/dev/null 2>&1 && exit 0

curl -fsSL 'https://claude.ai/install.sh' | bash
EOF


RUN cat > /om/scripts/install-codex <<'EOF' && chmod 664 /om/scripts/install-codex
#!/bin/bash
set -e

command -v codex >/dev/null 2>&1 && exit 0

npm i -g @openai/codex
EOF


RUN cat > /om/scripts/install-pi <<'EOF' && chmod 664 /om/scripts/install-pi
#!/bin/bash
set -e

command -v pi >/dev/null 2>&1 && exit 0

curl -fsSL https://pi.dev/install.sh | sh
EOF


RUN cat > /om/scripts/run-dbus <<'EOF' && chmod 664 /om/scripts/run-dbus
#!/bin/bash
set -ex

sudo mkdir -p /var/run/dbus /run/dbus
sudo dbus-daemon --system --nofork --nopidfile
EOF


RUN cat > /om/scripts/run-elasticsearch <<'EOF' && chmod 664 /om/scripts/run-elasticsearch
#!/bin/bash
set -euo pipefail

set -x

ELASTICSEARCH_VERSION="${ELASTICSEARCH_VERSION:-8.19.22}"

CACHE_DIR="${ELASTICSEARCH_CACHE_DIR:-$HOME/.cache/omdev/elasticsearch}"

case "$(uname -m)" in
    x86_64|amd64)
        ARCH=x86_64
        ;;
    aarch64|arm64)
        ARCH=aarch64
        ;;
    *)
        echo "Unsupported architecture: $(uname -m)" >&2
        exit 1
        ;;
esac

NAME="elasticsearch-$ELASTICSEARCH_VERSION-linux-$ARCH"
ARCHIVE="$CACHE_DIR/$NAME.tar.gz"
DIST_DIR="$CACHE_DIR/$NAME"

URL="https://artifacts.elastic.co/downloads/elasticsearch/$NAME.tar.gz"

STATE_DIR="${ELASTICSEARCH_STATE_DIR:-$CACHE_DIR/state-$ELASTICSEARCH_VERSION}"
DATA_DIR="${ELASTICSEARCH_DATA_DIR:-$STATE_DIR/data}"
LOGS_DIR="${ELASTICSEARCH_LOGS_DIR:-$STATE_DIR/logs}"

mkdir -p "$CACHE_DIR" "$DATA_DIR" "$LOGS_DIR"

# Serialize first-time setup in case multiple agents race to start it.
exec 9>"$CACHE_DIR/.lock"
flock 9

if ! test -s "$ARCHIVE"; then
    TMP="$ARCHIVE.tmp.$$"
    trap 'rm -f "$TMP"' EXIT

    curl \
        --fail \
        --location \
        --retry 3 \
        --retry-all-errors \
        --output "$TMP" \
        "$URL"

    EXPECTED_SHA512="$(
        curl \
            --fail \
            --location \
            --retry 3 \
            --retry-all-errors \
            "$URL.sha512" |
        awk '{print $1}'
    )"

    ACTUAL_SHA512="$(sha512sum "$TMP" | awk '{print $1}')"

    test "$ACTUAL_SHA512" = "$EXPECTED_SHA512"

    mv "$TMP" "$ARCHIVE"
    trap - EXIT
fi

if ! test -x "$DIST_DIR/bin/elasticsearch"; then
    TMP="$DIST_DIR.tmp.$$"
    trap 'rm -rf "$TMP"' EXIT

    rm -rf "$TMP"
    mkdir "$TMP"

    tar \
        -xzf "$ARCHIVE" \
        -C "$TMP" \
        --strip-components=1

    mv "$TMP" "$DIST_DIR"
    trap - EXIT
fi

flock -u 9
exec 9>&-

export ES_JAVA_OPTS="${ES_JAVA_OPTS:--Xms750m -Xmx750m}"

exec "$DIST_DIR/bin/elasticsearch" \
    -Ediscovery.type=single-node \
    -Expack.security.enabled=false \
    -Epath.data="$DATA_DIR" \
    -Epath.logs="$LOGS_DIR" \
    "$@"
EOF


RUN cat > /om/scripts/run-mysql <<'EOF' && chmod 664 /om/scripts/run-mysql
#!/bin/bash
set -ex

if ! sudo test -d /var/lib/mysql/mysql; then
    sudo mysqld --initialize-insecure --user=mysql
fi

sudo install -d -o mysql -g mysql -m 0755 /var/run/mysqld

sudo tee /var/run/mysqld/init.sql > /dev/null <<'SQL'
ALTER USER 'root'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'om';
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'om';
ALTER USER 'root'@'%' IDENTIFIED WITH caching_sha2_password BY 'om';
GRANT ALL ON *.* TO 'root'@'%' WITH GRANT OPTION;
CREATE USER IF NOT EXISTS 'om'@'%' IDENTIFIED BY 'om';
ALTER USER 'om'@'%' IDENTIFIED WITH caching_sha2_password BY 'om';
SQL

# --skip-log-error overrides the packaged config's log_error file and sends the error log to stderr instead. dumb-init
# rewrites SIGINT to SIGTERM, as mysqld ignores SIGINT but shuts down cleanly on SIGTERM.
exec sudo dumb-init --rewrite 2:15 mysqld --user=mysql --init-file=/var/run/mysqld/init.sql --skip-log-error
EOF


RUN cat > /om/scripts/run-postgres <<'EOF' && chmod 664 /om/scripts/run-postgres
#!/bin/bash
set -ex

PG_VERSION=$(ls /usr/lib/postgresql | sort -n | tail -n 1)
PG_BIN=/usr/lib/postgresql/$PG_VERSION/bin

if ! pg_lsclusters -h | grep -q "^$PG_VERSION main "; then
    sudo pg_createcluster "$PG_VERSION" main
fi

echo "ALTER USER postgres PASSWORD 'om';" | sudo runuser -u postgres -- "$PG_BIN/postgres" --single \
    -D "/var/lib/postgresql/$PG_VERSION/main" \
    -c "config_file=/etc/postgresql/$PG_VERSION/main/postgresql.conf" \
    postgres

exec sudo pg_ctlcluster "$PG_VERSION" main start --foreground
EOF


RUN cat > /om/scripts/run-s3mock <<'EOF' && chmod 664 /om/scripts/run-s3mock
#!/bin/bash
set -euo pipefail
set -x

S3MOCK_VERSION="${S3MOCK_VERSION:-5.2.3}"

CACHE_DIR="${S3MOCK_CACHE_DIR:-$HOME/.cache/omdev/s3mock}"
JAR="$CACHE_DIR/s3mock-$S3MOCK_VERSION-exec.jar"

URL="https://repo.maven.apache.org/maven2/com/adobe/testing/s3mock/$S3MOCK_VERSION/s3mock-$S3MOCK_VERSION-exec.jar"

mkdir -p "$CACHE_DIR"

# Serialize first-time setup in case multiple agents race to start it.
exec 9>"$CACHE_DIR/.lock"
flock 9

if ! test -s "$JAR"; then
    TMP="$JAR.tmp.$$"
    trap 'rm -f "$TMP"' EXIT

    curl \
        --fail \
        --location \
        --retry 3 \
        --retry-all-errors \
        --output "$TMP" \
        "$URL"

    mv "$TMP" "$JAR"
    trap - EXIT
fi

flock -u 9
exec 9>&-

exec java -jar "$JAR" "$@"
EOF


RUN (\
chmod a+x /om/scripts/* ;\
)

RUN (\
echo '\n\nexport PATH="$HOME/scripts:$PATH"' >> /om/.bashrc ;\
)


## entrypoint

WORKDIR /work

ENTRYPOINT [ \
  "dumb-init", \
  "--" \
]

CMD [ \
  "sh", \
  "-c", \
  "echo \"Ready\" && sleep infinity" \
]


## workdir

RUN (\
export WORKDIR='/work' ;\
\
set -ex ;\
umask 0002 ;\
\
sudo mkdir -p "$WORKDIR" ;\
sudo chown -R $(id -un) "$WORKDIR" ;\
sudo chgrp -R $(id -gn) "$WORKDIR" ;\
)


## chgrp

RUN (\
export CHGRP_ROOTS='/om /work' ;\
export CHGRP_GID='4317' ;\
\
set -ex ;\
umask 0002 ;\
\
find ${CHGRP_ROOTS} ! -group "${CHGRP_GID:-$(id -g)}" -exec chgrp -h "${CHGRP_GID:-$(id -g)}" {} + ;\
\
find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;\
)
