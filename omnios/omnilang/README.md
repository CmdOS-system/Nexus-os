# OmniLang

OmniLang is a planned statically typed systems language with ownership/borrowing, no mandatory garbage collector, explicit `unsafe`/FFI boundaries and a verified UIR. The first repository commit contains only the grammar and a design example. The compiler, lexer, parser, type checker, LLVM backend and runtime do not exist yet.

## Planned compiler pipeline

`source → lexer → parser/AST → typed HIR + ownership checks → verified UIR/SSA → LLVM AOT backends`

Initial target: x86_64 ELF user programs after OmniOS can load ELF. ARM64 follows after the kernel HAL. JIT is a later optional optimization and must use W^X executable memory. A UIR program is portable only where the language runtime and imported APIs exist; it does not make PE/Mach-O/DEX universally executable.
