<!--
SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors

SPDX-License-Identifier: LGPL-2.1-or-later
-->

# python-scsi

python-scsi is a SCSI initiator for Python. It builds CDBs, sends them to a
device, and parses the DATA-IN buffer back into plain dictionaries. Devices are
reachable over two transports:

* **SGIO** — `/dev/sg*` via `ioctl(SG_IO)`, needs
  [cython-sgio](https://github.com/python-scsi/cython-sgio)
* **iSCSI** — `iscsi://<server>/<iqn>/<lun>`, needs
  [cython-iscsi](https://github.com/python-scsi/cython-iscsi)

Both CDBs and DATA-IN/OUT buffers can be marshalled and unmarshalled without a
device present, which is how the test suite runs.

## Installing

    $ pip install pyscsi[sgio,iscsi]

The transports are optional extras; omit them to install the library alone. A
missing extra surfaces when you open a device, not at import.

Python 3.11 or newer is required.

## Documentation

* [DEVELOPMENT.md](DEVELOPMENT.md) — running the tests, the type checker, the
  development container, and verifying against real or emulated hardware
* [README-v2.md](README-v2.md) — the README for the 2.x versions

## Breaking changes in 3.0

| What changed | Affects you if you… |
|---|---|
| [Python 3.11 is the floor](#python-311-is-the-floor) | run 3.7–3.10 |
| [`pyscsi.utils.Enum` removed](#pyscsiutilsenum-is-removed) | import `Enum`, or call `.add()` / `.remove()` |
| [Tables no longer on the base class](#tables-no-longer-land-on-the-scsicommand-base) | read a table off a command that does not define it |
| [`OpCode._code` → `OpCode.value`](#opcode_code-is-now-opcodevalue) | touch `_code` |
| [`SCSICommand` is generic](#scsicommand-is-generic-in-its-result-type) | subclass it under a strict type checker |
| [CDB marshalling is per class](#marshall_cdb-and-unmarshall_cdb-are-classmethods) | call `marshall_cdb` on the base class |
| [The package is typed](#the-package-is-typed) | type-check against it — no action needed |

### Python 3.11 is the floor

3.7 through 3.10 are no longer supported.

### `pyscsi.utils.Enum` is removed

It was a custom metaclass over a dict, so a type checker could never see what
its members were. Use `Table` / `ValueTable` / `BitsTable` from
`pyscsi.utils.table`:

```python
from pyscsi.utils.enum import Enum        # 2.x
from pyscsi.utils.table import ValueTable # 3.0
```

The tables are immutable — `add()` and `remove()` are not carried over.

They keep the property that ruled out `enum.Enum`: SCSI tables contain duplicate
values by design (the 0xA3 service-action table alone holds 30 names across 17
values), and stdlib enum would silently alias them away.

### Tables no longer land on the `SCSICommand` base

Importing a command module used to `setattr` its tables onto the shared base, so
every command appeared to own every table. Reach for a table through the class
that defines it:

```python
Read10.DEVICE_TYPE     # 2.x -- worked by accident; now AttributeError
Inquiry.DEVICE_TYPE    # 3.0
```

### `OpCode._code` is now `OpCode.value`

```python
opcode._code           # 2.x
opcode.value           # 3.0
```

### `SCSICommand` is generic in its result type

Almost every command keys `result` by field name, but READ CD returns one entry
per sector and keys by LBA. `dict` is invariant in its key type, so no single
annotation describes both — each command binds its own:

```python
class Inquiry(SCSICommand[Dict[str, Any]]): ...
class ReadCd(SCSICommand[Dict[int, Dict[str, Any]]]): ...
```

Subclassing without a parameter still works at runtime. Under a strict type
checker it needs `SCSICommand[Any]`.

### `marshall_cdb` and `unmarshall_cdb` are classmethods

They previously read field maps that `__init__` had assigned to the *class*, so
constructing a second command changed how an earlier one decoded. On a concrete
command they behave as before. On the base they now return a correctly sized but
zero-filled CDB instead of silently reusing whichever command was built last:

```python
SCSICommand.marshall_cdb(d)   # 000000000000
Inquiry.marshall_cdb(d)       # 120180006000
```

### The package is typed

`py.typed` ships with the package, so annotations are visible to consumers. No
action needed.

## Fixes worth knowing about

These change what the library returns or accepts, on paths that previously had
no test coverage:

* **REPORT LUNS** truncated the last LUN of a conformant parameter list by four
  bytes when unmarshalling, and understated the length by four when marshalling.
* **EXTENDED COPY** segment descriptor type codes 01h and 0Ch (copy stream to
  block) raised `AttributeError` instead of encoding a descriptor, in both the
  SPC-4 and SPC-5 implementations.
* **MODE SELECT (10)** raised `TypeError` on every call.
* **WRITE SAME (16)** with NDOB set failed over iSCSI, which sized the transfer
  with `len(cmd.dataout)` on a command that deliberately has no data-out buffer.

## Tools

`tools/` and `examples/` hold programs written against the API — `inquiry.py`
sends INQUIRY commands, `mtx.py` operates a media changer along the lines of the
`mtx` utility.

## Getting the sources

    $ git clone git@github.com:python-scsi/python-scsi.git

The project is hosted at https://github.com/python-scsi/python-scsi.

## Mailing list

https://groups.google.com/forum/#!forum/python-scsi

## License

LGPL-2.1-or-later. See `LICENSE` for the full text.
