rm -f /etc/apt/apt.conf.d/docker-clean ;
rm -f /etc/dpkg/dpkg.cfg.d/excludes ;

export DEBIAN_FRONTEND=noninteractive ;
apt-get update ;

apt-get install -y locales ;
locale-gen en_US.UTF-8 ;

apt-get upgrade -y ;

if [ "$(dpkg-divert --truename /usr/bin/man)" = '/usr/bin/man.REAL' ]; then
  rm -f /usr/bin/man ;
  dpkg-divert --quiet --remove --rename /usr/bin/man ;
fi ;

apt-get install -y --reinstall $(dpkg-query -W -f='${binary:Package} ${db:Status-Status}\n' | awk '$2=="installed"{print $1}') ;

apt-get install -y man-db manpages manpages-dev ;
rm -f /etc/update-motd.d/60-unminimize ;

apt-get install -y apt-utils ;
