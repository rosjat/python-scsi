<!--
SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors

SPDX-License-Identifier: LGPL-2.1-or-later
-->

# Development Information

You can install all tools needed for developing the package by using
the `dev` extra:

    python-scsi $ pip install -e .[dev]

This will include test and verification tools, as well as all the
necessary packages to build a new release.

## pre-commit

This repository uses [pre-commit](https://pre-commit.com/) to maintain a
consistent codebase. The tool is installed as part of the `dev` extra.

To activate the pre-commit hooks, you should use:

    python-scsi $ pre-commit install

which will set up the hooks for the current repository.

## Unit Testing

The tests directory contains unit tests for python-scsi. They use a mock
device and need no hardware:

    python-scsi $ pip install -e .[dev]
    python-scsi $ pytest

Run them from the repository root — the tests import `tests.mock_device`.

Type checking is a separate step:

    python-scsi $ mypy

`strict = true` applies to the whole package and the test suite, with no
per-module exemptions and no disabled error codes. A new module is checked from
the moment it is added; there is no list to opt into.

`python_version` in `pyproject.toml` pins the analysis target to 3.11, so a
bare `mypy` checks the floor whatever interpreter you run it under. Pass
`--python-version` to check another:

    python-scsi $ mypy --python-version 3.14

Two things are worth knowing before writing a command class:

* `SCSICommand` is generic in its result type — `SCSICommand[Dict[str, Any]]`
  for a command whose result is keyed by field name. See the note in
  `scsi_command.py` for why a single type does not work.
* Zero-argument `super()` and `typing.Generic` both work in a command class, but
  only because `SCSIDeviceCommandExceptionMeta` builds each class once. It used
  to build twice, which broke both.

## Development container

Everything above can be run in a container instead — the only route on a host
without Python. The image adds both SCSI transports, `sg3_utils`, `tgt` and the
verification harness, and mounts the repository at `/src`.

`podman` and `docker` are interchangeable in every command below.

### Getting the image

CI publishes it, so pulling is usually enough:

    podman pull ghcr.io/python-scsi/python-scsi-dev:latest

A release tag publishes a matching `:vX.Y.Z`. The commands below say
`python-scsi-dev`; use the full `ghcr.io/...` reference, or retag it locally.

To build it instead:

    podman build -f containers/Containerfile -t python-scsi-dev containers/

### Choosing a runtime

One image carries 3.11 through 3.14, each in its own virtualenv under
`/opt/venv/<version>`. Select one by path:

    podman run --rm -v "$PWD:/src:z" python-scsi-dev /opt/venv/3.13/bin/pytest

The harness commands read `PYSCSI_PYTHON` instead:

    podman run --rm -v "$PWD:/src:z" -e PYSCSI_PYTHON=3.13 \
        python-scsi-dev pyscsi-verify-iscsi

A bare `pytest`, `python` or `mypy` uses 3.11. `mypy`, `pre-commit` and `build`
are installed there only, so check another version from that virtualenv rather
than installing mypy again — `--python-version` sets the analysis target and
`--python-executable` resolves that runtime's packages:

    podman run --rm -v "$PWD:/src:z" python-scsi-dev \
        mypy --python-version 3.14 --python-executable /opt/venv/3.14/bin/python

Omitting `--python-version` re-checks 3.11 without saying so.

### The transports

`cython-sgio` and `cython-iscsi` are built from `master` of their repositories,
not installed from PyPI. Pin them with build arguments:

    podman build -f containers/Containerfile \
        --build-arg SGIO_REF=<sha> --build-arg ISCSI_REF=<sha> \
        -t python-scsi-dev containers/

`master` caches on the literal string, so pass a SHA or `--no-cache` to pick up
new commits.

### The whole matrix at once

`pyscsi-matrix` runs the suite on every runtime in turn and prints a summary.
Arguments are passed through to pytest.

    podman run --rm -v "$PWD:/src:z" python-scsi-dev pyscsi-matrix -q
    podman run --rm -v "$PWD:/src:z" python-scsi-dev pyscsi-matrix -k inquiry

### Everyday commands

Each mounts the repository at `/src`:

| Task | Command |
|---|---|
| tests | `podman run --rm -v "$PWD:/src:z" python-scsi-dev pytest -vv` |
| one test | `podman run --rm -v "$PWD:/src:z" python-scsi-dev pytest -k inquiry` |
| type check | `podman run --rm -v "$PWD:/src:z" python-scsi-dev mypy` |
| lint | `podman run --rm -v "$PWD:/src:z" python-scsi-dev pre-commit run --all-files` |
| shell | `podman run --rm -it -v "$PWD:/src:z" python-scsi-dev bash` |
| build sdist+wheel | `podman run --rm -v "$PWD:/src:z" python-scsi-dev python -m build` |

On Windows `$PWD` becomes the drive-lettered path with forward slashes, for
example `-v "D:/Projekte/python-scsi:/src:z"`. The `:z` suffix is an SELinux
relabel, harmless where SELinux is not in use.

Nothing in the container writes to the mount, except `python -m build`:
setuptools drops `build/` and `*.egg-info/` next to the sources whatever
`--outdir` says. To keep the tree clean:

    podman run --rm -v "$PWD:/src:z" python-scsi-dev bash -c \
        'python -m build --outdir /tmp/dist /src && cp /tmp/dist/* /src/dist/; \
         rm -rf /src/build /src/*.egg-info'

### Verifying against a real device

`pyscsi-verify-tools` runs the applicable tools and examples against a device,
read-only, and reports pass, fail or skip for each. It also runs `sg_inq`,
`sg_readcap` and `sg_modes` for comparison.

    podman run --rm -v "$PWD:/src:z" \
        --device /dev/sg0 --cap-add=SYS_RAWIO \
        python-scsi-dev pyscsi-verify-tools /dev/sg0

`SYS_RAWIO` is what the `SG_IO` ioctl checks; `--device` alone is not enough.
`/dev/sg*` needs root or the `disk` group, so rootless podman cannot reach a
device the invoking user cannot.

With no SCSI hardware to hand, the kernel can emulate one:

    $ sudo modprobe scsi_debug dev_size_mb=8

`ptype=0x14` gives a host-managed zoned device, the only way to exercise the
ZBC commands. `ptype=1` and `ptype=5` change only the INQUIRY device type — the
tape and MMC command sets are not implemented, and there is no changer type.
Use `tgt` for those.

### Verifying over iSCSI

`pyscsi-verify-iscsi` stands up emulated targets with `tgt`, one LUN per device
type, and drives the tools against all of them:

    podman run --rm -v "$PWD:/src:z" python-scsi-dev pyscsi-verify-iscsi

| LUN | Device type | Opcode table |
|---|---|---|
| 1 | disk | `sbc` |
| 2 | media changer | `smc` |
| 3 | tape | `ssc` |
| 4 | cd/dvd | `mmc` |

This is the only coverage the `ssc`, `mmc` and `smc` tables and the iSCSI
transport get; the unit tests use a mock device and a real `/dev/sg*` is
usually a disk. It needs no privileges and no kernel modules.

To start the targets alone. `pyscsi-tgt-setup` returns once the LUNs are
configured, so it needs something to hold the container open:

    podman run --rm -p 3260:3260 python-scsi-dev \
        bash -c 'pyscsi-tgt-setup && sleep infinity'

### Settings

| Variable | Default | Purpose |
|---|---|---|
| `PYSCSI_SRC` | `/src` | where the repository is mounted |
| `PYSCSI_IQN` | `iqn.2026-01.org.pyscsi:test` | emulated target name |
| `PYSCSI_PORTAL` | `127.0.0.1` | iSCSI portal to connect to |

Also inside the image: `sg_inq`, `sg_modes`, `sg_readcap`, `sg_rep_zones` and
the rest of `sg3_utils`; `tgtd` and `tgtadm`; and `iscsi-ls` from `libiscsi`.

## Continuous Integration

- `test.yml` — pytest and mypy across Python 3.11 to 3.14
- `pre-commit.yml` — the same hooks you get locally
- `pypi.yml` — builds and publishes, on release tags only
- `container.yml` — builds and publishes the image, only when the Containerfile
  or the workflow changes, plus manually from the Actions tab
- `container-release.yml` — the same on a release tag, adding a `:vX.Y.Z` image

The first two run on every push and pull request.

## Releasing

[Setuptools](https://setuptools.readthedocs.io/) is used to create the released
packages:

    python-scsi $ pip install -e .[dev]
    python-scsi $ git clean -fxd
    python-scsi $ git tag -a vX.Y.Z
    python-scsi $ python -m build

The `git tag` command marks the version that
[setuptools-scm](https://github.com/pypa/setuptools_scm/) uses to derive the
version recorded in the source and wheel packages. Tags are plain `vX.Y.Z` and
follow [Semantic Versioning](https://semver.org/). Never edit a version by hand.

Pushing a `v*` tag triggers the publish workflow, which refuses to publish a tag
that is not merged into `master`.

## Repository Layout

The repository follows a (mostly) standard layout for Python repositories:

 * `.gitattributes` pins every text file to LF, in the index and the working
   tree, so a checkout on Windows and a container on Linux agree.
 * `.gitignore` is set to ignore generated files from Python testing and usage.
 * `.pre-commit-config.yaml` contains the configuration for
   [pre-commit](https://pre-commit.com/) and its hooks.
 * `pyproject.toml` holds the package metadata and the configuration for
   setuptools, setuptools-scm, pytest, mypy and isort.
 * `README.md` documents 3.0 onwards and lists the breaking changes;
   `README-v2.md` is the retired 2.x one.
 * `containers` contains the development container and its harness.
 * `pyscsi` contains the source code of the module that is actually installed
   by pip.
 * `tools` and `examples` contain Python entrypoints showing usage of the
   library.
 * `tests` contains the unittests to validate the correctness of the library.
