find ${CHGRP_ROOTS} ! -group "$(id -g)" -exec chgrp -h "$(id -g)" {} + ;

find ${CHGRP_ROOTS} ! -type l \( \
  \( -perm -u=r ! -perm -g=r \) -o \( ! -perm -u=r -perm -g=r \) -o \
  \( -perm -u=w ! -perm -g=w \) -o \( ! -perm -u=w -perm -g=w \) -o \
  \( -perm -u=x ! -perm -g=x \) -o \( ! -perm -u=x -perm -g=x \) \
\) -exec chmod g=u {} + ;
