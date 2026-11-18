# Complete offline source build

This archive contains the editable application and the exact vendor source subset used by Two-port NUCLEO-L476RG IO-Link physical station. It includes required headers, startup code, linker script, HAL sources, protocol stack sources, licenses, source revisions and per-file hashes. It excludes compiled outputs, caches, Git history and unrelated vendor examples.

Install the recorded Debian arm-none-eabi GCC 13.2.1 toolchain, Python 3 and Make. The toolchain.json file identifies the exact compiler and selected library bytes used by the accepted build. Extract the archive into a new directory, then run from its root:

~~~sh
python3 source/build.py --output-dir /absolute/path/to/new-build --verify-release
~~~

The build verifies every vendor file and its complete inventory before invoking the normal Makefile dependency gate. The --verify-release option requires the resulting flash BIN and every ELF PT_LOAD address, byte range, memory extent, flag and entry point to match the accepted physical firmware exactly. ELF debug paths can change after relocation; the result records both ELF hashes and their actual equality. Existing accepted ELF files retain their original recorded hashes.

For an application edit, change the application source and omit --verify-release; the same vendor integrity checks still apply. The output receipt records source hashes before and after the build. Changing a dependency requires an intentional new source export and corresponding provenance; editing a vendor file without updating that export fails verification.

The archive does not contain fabricated hardware test results. Its rebuild receipt proves source-to-flash identity; the separate runtime and hardware qualification records define execution and physical scope.

Use --target master or --target device to build one image. The same device image runs on both physical device nodes; the existing runtime provides distinct MCU UID fixtures. No legacy direct-UART simulator image is used by this source package.
