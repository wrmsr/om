# Where the container sees the files a run stages for it.
CONTAINER_STAGING_DIR = '/dockerdev'

ID_LABEL = 'om.dockerdev'

CACHE_VOLUME = 'om-dockerdev-cache'
CACHE_DIR = '/cache'

PERSIST_VOLUME = 'om-dockerdev-persist'
PERSIST_DIR = '/persist'
