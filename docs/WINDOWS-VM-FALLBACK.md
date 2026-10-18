# Comprobación previa de Windows virtualizado para Office

Actualizado:17/10/2026, Bogotá. Alternativa de laboratorio si Office actual bajo Wine sigue bloqueado. **Este componente no instala Windows ni acredita Word.**

## Fuentes y alcance

- [API KVM de Linux](https://docs.kernel.org/virt/kvm/api.html): abrir el dispositivo y consultar KVM_GET_API_VERSION; la API estable debe devolver12. Este componente no invoca KVM_CREATE_VM.
- [WinApps](https://github.com/winapps-org/winapps) y su [preparación de VM](https://github.com/winapps-org/winapps/blob/main/docs/docker.md): aplicaciones ejecutadas en Windows y presentadas con FreeRDP. Es un backend diferente de Wine; su integración debe probarse en Nexus.

`python3 agent/windows_vm_preflight.py` consulta arquitectura, acceso a KVM, memoria disponible, espacio libre del sistema de archivos personal y presencia de QEMU, gestor de VM y FreeRDP. No crea máquinas ni discos, instala paquetes o cambia permisos. Diferencia dispositivo ausente, permiso denegado y API incorrecta. Cierra el descriptor incluso si falla la consulta.

Encontrar un ejecutable no confirma su versión ni acceso a su servicio. Los recursos observados no se reservan. `static_prerequisites_detected` nunca demuestra compatibilidad con Office; Windows y Word mantienen sus campos de aceptación en falso.

## Evidencia actual

Cuatro pruebas locales aprobadas. El entorno local carece de /dev/kvm y herramientas VM/FreeRDP; no extrapolar ese resultado al equipo del usuario.

Run39092631455 success; artefacto12123665679 descargado y revisado. El runner dispone de unos15.6GiB de RAM total,85.8GiB libres, Docker y Podman. /dev/kvm devuelve permiso denegado, no ausencia. Faltan QEMU y FreeRDP. Ese verde significa que la inspección funcionó; los requisitos siguen incompletos.

Se añade una segunda consulta de solo lectura con el administrador del runner para diferenciar permisos del usuario y disponibilidad real de KVM. No modifica grupos, permisos, módulos del kernel ni archivos de configuración. Se conservan ambos JSON. No es un patrón de ejecución privilegiada propuesto para el usuario final.

Run39092711537 success; artefacto12123421036 descargado y revisado: usuario normal recibe permiso denegado y consulta administrativa devuelve KVM API12 disponible. Se confirma acceso posible a aceleración en ese runner; todavía faltan QEMU y FreeRDP. No se creó ninguna VM, instaló Windows o ejecutó Word. Siguiente paso técnico: preparar herramientas y acceso de laboratorio apropiado, y solo entonces instalar Windows/Office en disco virtual desechable.

## Siguiente entrega

Inspeccionar ambos informes; elegir un entorno apropiado y configurar el backend en un laboratorio aislado. Después instalar Windows/Office legítimos en disco virtual desechable y probar RemoteApp y Word. No exponer RDP públicamente ni guardar credenciales en logs.

Criterios finales: [OFFICE-DESKTOP-ACCEPTANCE.md](OFFICE-DESKTOP-ACCEPTANCE.md). Global≈38%, Windows50%, Word0/7. Este preflight no aumenta los porcentajes.


## Siguiente prueba: ejecución KVM real, sin Windows

Se añade job aislado `exercise-kvm`: instala QEMU y FreeRDP3 en runnerUbuntu24.04 desechable y ejecuta `agent/tests/windows_vm_kvm_smoke.py` con opt-in explícito. Crea máquina q35/KVM,256MiB y una CPU virtual, sin discos, ISO ni red; consultaQMP para confirmar aceleración, continúaCPU, confirma estado running, pausa y cierraQEMU limpiamente. Conserva versiones y resultadoJSON. FreeRDP3 se verifica con /version, sin conectarse a ningúnservidor.

Fuentes: esquemaQEMU qapi/run-state.json, referenciaQMP query-kvm/query-status/cont/stop/quit, paqueteoficialUbuntu freerdp3-x11. La API/query disponible no basta: esta prueba exige ejecución deCPU virtual. El estado running de esta máquina sinOS no es arranqueWindows, RemoteApp o aceptaciónWord. No hay copia deWindows/Office, licencia ocredenciales en esta prueba. Guardias deentornodesechable y compilaciónPython comprobadaslocalmente; ejecuciónKVM realpendiente. No se añaden herramientas a laISO deNexus por este ensayo.


## Ejecución real aprobada

Run39094951752 y Fast Checks39094953980 finalizaron con éxito. Se descargó e inspeccionó el artefacto12123709566: QEMU8.2.2, FreeRDP3.32.1, KVM habilitado, CPU virtual en estado running y luego paused, salida limpia. El resultado declara Windows y Word sin validar. La máquina no tenía discos, red ni sistema operativo. Evidencia guardada en docs/evidence/2026-10-17/kvm-engine-result.json.

Se supera el requisito de ejecutar el motor de virtualización en el runner. Aún faltan Windows, Office, conexión RemoteApp e integración en Nexus; el resultado no mide rendimiento ni compatibilidad de aplicaciones. No se han instalado estos paquetes en la ISO de Nexus.
