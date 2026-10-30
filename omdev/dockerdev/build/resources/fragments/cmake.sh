sudo apt install -y ca-certificates gpg wget ;

test -f /usr/share/doc/kitware-archive-keyring/copyright || \
  wget -O - 'https://apt.kitware.com/keys/kitware-archive-latest.asc' 2>/dev/null | \
  gpg --dearmor - | \
  sudo tee /usr/share/keyrings/kitware-archive-keyring.gpg >/dev/null ;

echo 'deb [signed-by=/usr/share/keyrings/kitware-archive-keyring.gpg] https://apt.kitware.com/ubuntu/ noble main' | \
  sudo tee /etc/apt/sources.list.d/kitware.list >/dev/null ;

sudo apt update ;
sudo apt install -y kitware-archive-keyring ;

sudo apt update ;
sudo apt install -y cmake ;
