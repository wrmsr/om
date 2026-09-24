sudo mkdir -p /etc/apt/keyrings ;

curl -fsSL \
  'https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x738BEB9321D1AAEC13EA9391AEBDF4819BE21867' |
  sudo tee /etc/apt/keyrings/mozillateam.asc >/dev/null ;

echo "
Types: deb\n
URIs: https://ppa.launchpadcontent.net/mozillateam/ppa/ubuntu/\n
Suites: noble\n
Components: main\n
Signed-By: /etc/apt/keyrings/mozillateam.asc\n
" | sudo tee /etc/apt/sources.list.d/mozillateam.sources >/dev/null ;

echo "
Package: *\n
Pin: release o=LP-PPA-mozillateam\n
Pin-Priority: 1001\n
\n
Package: firefox\n
Pin: version 1:1snap1-0ubuntu2\n
Pin-Priority: -1\n
" | sudo tee /etc/apt/preferences.d/mozilla-firefox ;

sudo apt-get update ;
sudo apt-get install -y firefox ;

echo 'Unattended-Upgrade::Allowed-Origins:: "LP-PPA-mozillateam:${distro_codename}";' |
  sudo tee /etc/apt/apt.conf.d/51unattended-upgrades-firefox ;
