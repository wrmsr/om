# syntax=docker/dockerfile:1

##
# Build-only image producing portable (manylinux) linux wheels.
#
# Package-name agnostic: builds whatever project is at the context root, selects wheels per interpreter by filename
# tags, and derives import names from each dist's own metadata.
#
# pypa publishes per-arch image repos (there are no multiarch manifests), so the base is selected via TARGETARCH. Once
# settled, pin these by digest:
#   FROM quay.io/pypa/manylinux_2_28_x86_64@sha256:... AS base-amd64

ARG TEST_IMAGE=python:3.14-slim

FROM quay.io/pypa/manylinux_2_28_x86_64 AS base-amd64
FROM quay.io/pypa/manylinux_2_28_aarch64 AS base-arm64

##

FROM base-${TARGETARCH} AS build

ARG TARGETARCH

# Interpreters to wheel for, as /opt/python/ dirnames. cp314-cp314t is the freethreaded build.
ARG PYTHONS="cp314-cp314 cp314-cp314t"

WORKDIR /src
COPY . .

# One wheel per interpreter - `python -m build` targets whichever interpreter invokes it, hence the loop. The pip cache
# lives in a buildkit cache mount so repeat builds don't refetch build/setuptools/wheel.
RUN --mount=type=cache,target=/root/.cache/pip,id=pip-linux-${TARGETARCH} \
    set -eux; \
    for py in ${PYTHONS}; do \
        pybin="/opt/python/${py}/bin"; \
        "${pybin}/python" -m pip install build; \
        "${pybin}/python" -m build --wheel --outdir /tmp/wheels .; \
    done

# Audit + retag linux_* -> manylinux_2_28_*, vendoring any external shared libs. This *fails the build* if a .so leaks
# symbol versions newer than the manylinux_2_28 policy allows.
RUN set -eux; \
    for whl in /tmp/wheels/*.whl; do \
        auditwheel repair "${whl}" --wheel-dir /out; \
    done; \
    ls -l /out

# Package-name-agnostic import check: reads each installed dist's top_level.txt and imports every module it declares. On
# freethreaded builds it also asserts the imports did not silently re-enable the GIL (i.e. the exts actually declare
# Py_mod_gil).
COPY <<'CHECKEOF' /check.py
import importlib
import importlib.metadata as md
import sys
import sysconfig

for dist in sys.argv[1:]:
    tl = (md.distribution(dist).read_text('top_level.txt') or dist.replace('-', '_')).split()
    for name in tl:
        mod = importlib.import_module(name)
        print('imported', mod.__name__, 'from', mod.__file__)

assert not (sysconfig.get_config_var('Py_GIL_DISABLED') and sys._is_gil_enabled())
CHECKEOF

# Check every repaired wheel with its own interpreter. Wheels are selected per interpreter via the {python}-{abi} tag
# pair in their filenames (which is exactly the /opt/python dirname), installed by *path* so no dist name is needed, and
# dist names for the import check are recovered from the filenames. `--no-deps` keeps it hermetic - drop it if a package
# has hard runtime deps needed at import time.
#
# NB: must run *outside* /src - the cwd/script dir lands on sys.path, so the copied source tree would shadow the
# installed packages.
RUN set -eux; \
    cd /tmp; \
    for py in ${PYTHONS}; do \
        pybin="/opt/python/${py}/bin"; \
        "${pybin}/python" -m pip install --no-deps /out/*-"${py}"-*.whl; \
        dists="$(for w in /out/*-"${py}"-*.whl; do basename "${w}" | cut -d- -f1; done | sort -u)"; \
        "${pybin}/python" /check.py ${dists}; \
    done

##

# Smoke test on a different distro + glibc than the build env (debian vs alma8) to back up the portability claim.
# TEST_TAG selects which wheels this python can run; official docker python images have no freethreaded variant, so the
# t wheels only get the build-stage check above.
FROM ${TEST_IMAGE} AS test

ARG TEST_TAG=cp314-cp314

COPY --from=build /check.py /check.py
COPY --from=build /out /wheels

RUN set -eux; \
    cd /tmp; \
    pip install --no-deps /wheels/*-"${TEST_TAG}"-*.whl; \
    dists="$(for w in /wheels/*-"${TEST_TAG}"-*.whl; do basename "${w}" | cut -d- -f1; done | sort -u)"; \
    python /check.py ${dists}; \
    echo 'smoke test ok'

##

# Final stage contains only the wheels; routing them through `test` forces the smoke test to run whenever `dist` is
# targeted.
FROM scratch AS dist

COPY --from=test /wheels /
