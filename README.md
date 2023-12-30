# machine68k - m68k Emulator and Machine Binding for Python

- written by Christian Vogelgsang <chris@vogelgsang.org>
- under the GNU Public License V2

## Introduction

`machine68k` is a Python package that offers a system binding for
the [Musashi][1] Motorola 68000 CPU emulator with memory binding and
support for ALine opcode exception traps.

The package is currently used by the [amitools][2] project and
supplies the CPU emulation for `vamos`.

## Prerequisites

- Python >= ```3.8```
- [pip3][3]

## Optional Packages

- [cython][4]: (version >= **3.0.0**) required to rebuild the native module

[1]: https://github.com/kstenerud/Musashi
[2]: https://github.com/cnvogelg/amitools
[3]: https://packaging.python.org/en/latest/tutorials/installing-packages/
[4]: https://cython.org

## Installation

### Stable/Release Version

```bash
pip3 install machine68k
```

Note:

- on Linux/macOS may use ``sudo`` to install for all users
- requires a host C compiler to compile the extension.
- the version may be a bit outdated. If you need recent changes use the
  current version.

### Current Version from GitHub

Ensure you have Cython installed:

```bash
pip3 install cython
```

Then install `machine68k` directly from the git repository:

```bash
pip3 install -U git+https://github.com/cnvogelg/machine68k.git
```

Or if you have a local clone of the repository:

```bash
pip3 install .
```

Note:

- This will install the latest version found in the github repository.
- You find the latest features but it may also be unstable from time to time.
- Repeat this command to update to the latest version.

### Developers

- Follow this route if you want to hack around with the codebase
- Clone the Git repo: [machine68k@git](https://github.com/cnvogelg/machine68k)
- Ensure you have Cython installed:

```bash
pip3 install cython
```

- Enter the directory of the cloned repo and install via pip:

```bash
pip3 install -U -e .
```

This install `machine68k` in your current Python environment but takes the
source files still from this repository. So you can change the code there
and directly test the machine.
