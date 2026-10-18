# Windows virtualizado: comprobación previa para Office

Actualizado17/10/2026 Bogotá. Alternativa de laboratorio si Office actual bajo Wine sigue bloqueado. **No instala Windows ni acredita Word.**

Fuentesprimarias: [APIKVM Linux](https://docs.kernel.org/virt/kvm/api.html), [WinApps arquitectura](https://github.com/winapps-org/winapps), [preparaciónWindowsVM](https://github.com/winapps-org/winapps/blob/main/docs/docker.md). WinApps presenta apps ejecutadas en Windows medianteFreeRDP; es backenddiferente deWine. La integración, recursos y ejecuciónWord debenprobarseenNexus.

`python3 agent/windows_vm_preflight.py` consulta arquitectura, KVM_GET_API_VERSION12, memoria disponible, espacio de sistema dearchivoshome y presencia deQEMU/gestorVM/FreeRDP. No creaVM ni escribe discos/configuraciones; tampoco instala paquetes, cambia grupos/permisos o comprueba licencias. Diferencia dispositivoausente, permisosdenegados yAPIincorrecta; cierra descriptor incluso si ioctl falla. Las métricasderesursos no reservan ni garantizan capacidad. Encontraruncomando no confirma versiónFreeRDP3, daemonhabilitado o accesoalgestor. `static_prerequisites_detected` noescompatibilidadOffice.

Cuatro pruebaslocales aprobadas. Inspección real del entorno local: /dev/kvm ausente, sinQEMU, gestorVM niFreeRDP. Eso impide aceptaresta ruta eneseentorno, no describeelPCdelusuario. El workflow `Nexus Windows VM Prerequisites` observará directamenteunrunnerUbuntu (fuera del contenedorWine) sinmodificarlo y guardaráJSON; resultadoCIpendiente.

Siguiente: inspeccionarJSON delrunner, decidir entornoapropiado y backend; prepararWindows/Officelegítimos en disco virtualdescartable; probarRDP/RemoteApp y documentoWord real. No abrirpuertos públicos, volcarcredenciales o usarKVM_CREATE_VM en estepreflight. Criterios finales: [OFFICE-DESKTOP-ACCEPTANCE.md](OFFICE-DESKTOP-ACCEPTANCE.md). Global≈38%, Windows50%, Word0/7, sinincrementoporestecomponente.
