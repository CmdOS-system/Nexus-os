# WebAssembly y WASI

## Ubicación y límite de confianza

El ejecutor WASM y el host WASI son procesos de **usuario**, nunca módulos dentro del kernel. El kernel les ofrece memoria aislada, IPC y handles con capacidades limitadas. El runtime valida el módulo, crea su memoria lineal y satisface solo las interfaces WASI que la política del usuario haya autorizado. Un módulo no recibe punteros de kernel ni acceso implícito a archivos, red, reloj o procesos.

```text
archivo .wasm → OmniLoader (reconoce candidato) → validador/runtime en usuario
                                                  │ imports WASI autorizados
                                                  ▼
                              host WASI → IPC/handles → OmniKernel
```

## Alcance incremental

1. Primera fase: reconocer `\0asm` y rechazar versiones/formatos no soportados antes de instanciar.
2. Elegir un runtime mantenido en modo intérprete para el primer prototipo; comparar compatibilidad, consumo y auditorías antes de fijar dependencia. El JIT queda desactivado inicialmente.
3. Empezar con un perfil WASI versionado; probar WASI 0.2/component model y mantener WASI 0.3 Preview como experimento hasta que se estabilice.
4. Exponer stdio y un directorio de archivos explícitamente concedido. Añadir red, reloj, aleatoriedad y procesos solo con capacidades, cuotas y pruebas separadas.
5. Poner límites de memoria, pila, instrucciones/fuel y tiempo; cancelar módulos que excedan sus cuotas.

Una aplicación web que usa WebAssembly y DOM/Web APIs no se vuelve una aplicación WASI por el hecho de incluir `.wasm`. WASI cubre interfaces de sistema; la ejecución de una PWA sigue necesitando navegador o shell web con DOM, fetch, almacenamiento y APIs que la aplicación use.

## Pruebas previstas

- Módulo válido y módulo truncado o con versión desconocida.
- Import WASI no concedido y acceso a ruta fuera del directorio permitido.
- Agotamiento de memoria/fuel y terminación limpia.
- Suite de conformidad correspondiente a la versión WASI fijada.

## Referencias

- WASI: https://github.com/WebAssembly/WASI
- Overview de WASI 0.2: https://github.com/WebAssembly/WASI/blob/main/specifications/wasi-0.2.12/Overview.md
- Capacidades WASI: https://github.com/WebAssembly/WASI/blob/main/docs/Capabilities.md
- Formato core WASM: https://webassembly.github.io/spec/core/binary/modules.html
