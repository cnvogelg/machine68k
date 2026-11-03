# Change Log

## [0.5.0][6] (2026-11-03)

* added support for Python 3.14 and 3.15
* fixed MC68881 extended arithmetic for exponent-zero values (#10)
* fixed Windows opcode table over-read and JMP/CAS opcode collision (#12, #13)
* fixed Windows build tool executable path (#11)
* updated build-system requirements for current package metadata (#14)
* renamed the GitHub Actions test workflow (#15)
* contributors: Thomas Dye (#11, #12, #13) and Stefan Reinauer (#14, #15)

## [0.4.1][5] (2025-12-21)

* fix for Python 3.12 and rpyc
* added support for Python 3.13

## [0.4.0][4] (2025-12-20)

* rewrote machine's execute
* rewrote and simplified traps
* more tests
* add support for rmachine68k
* added greenlet support
* added benchmarks
* applied mushashi time slice fix (#107)
* removed Python 3.7 and added 3.12

## [0.3.0][3] (2024-08-25)

* fixed build with newer setuptools

## [0.2.0][2] (2024-02-18)

* Updated musashi code base to 2158f7081001f89145283d291ee501321e8dc26d
  from (2024-02-08)

## [0.1.0][1] (2023-12-31)

* First public release
* Moved machine implementation from `amitools`


[1]: https://github.com/cnvogelg/machine68k/tree/v0.1.0
[2]: https://github.com/cnvogelg/machine68k/tree/v0.2.0
[3]: https://github.com/cnvogelg/machine68k/tree/v0.3.0
[4]: https://github.com/cnvogelg/machine68k/tree/v0.4.0
[5]: https://github.com/cnvogelg/machine68k/tree/v0.4.1
[6]: https://github.com/cnvogelg/machine68k/tree/v0.5.0
