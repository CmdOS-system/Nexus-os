# Nexus OS — compatibilidad Windows como prioridad central

Decisión explícita del usuario, 2026-10-17: el valor central es poder usar aplicaciones Windows en Nexus. La compatibilidad no queda detrás del acabado visual, voz, TV o radio. El escritorio necesita ser utilizable; su pulido completo no bloquea iniciar el laboratorio Windows.

## Objetivo verificable

Instalar aplicaciones Windows reales desde fuentes oficiales, ejecutarlas en Nexus, completar tareas útiles, guardar/reabrir datos y mantener funcionamiento tras reinicio. No declarar compatibilidad por leer cabeceras PE, arrancar winecfg o abrir una ventana sin usar sus funciones. Alcance por aplicación/versión/arquitectura, no compatibilidad universal.

## Orden de trabajo

1. **P0 inmediato: laboratorio de compatibilidad Debian 13.** Revisar código y documentación existentes; instalar Wine con dependencias y arquitectura adecuadas en entorno desechable. Registrar versiones y crear prefijos separados por aplicación. Comprobar un ejecutable Windows propio de prueba; después aplicaciones oficiales sencillas como 7-Zip y Notepad++, fijando versión y hash al descargar. No considerar el ejecutable de prueba evidencia suficiente de aplicaciones comerciales.
2. **P0: una aplicación difícil importante para el usuario.** Identificar nombre, versión, arquitectura y tarea imprescindible. Reproducir fallo, reunir logs/API faltantes y elegir corrección fundada. Probar instalación, apertura, tarea útil, archivo guardado/reabierto, cierre y reinicio. Si resulta incompatible, registrar bloqueo y alternativa explícita, sin ocultarlo detrás de una app sencilla.
3. **P0: integrar la experiencia Nexus.** Abrir .exe/.msi con asistente comprensible, elegir perfil apropiado, gestionar prefijos/dependencias, mostrar errores y desinstalar. Preguntar antes de ejecutar un instalador descargado; no asociar doble clic a ejecución silenciosa de cualquier archivo. Ejecutar como usuario sin privilegios. Wine/prefijos no son una frontera de seguridad suficiente: aislar acceso a archivos y red según necesidades.
4. **P0: persistencia y prueba en Nexus instalado.** Instalar en QCOW2 desechable, arrancar sin ISO, conservar app/perfil/documentos y repetir tareas. No esperar a completar el diseño para trabajar este hito. No tocar discos físicos.
5. **P1: ampliar matriz.** Productividad, utilidades, apps empresariales y juegos por familias; versiones x86/x64 evaluadas por separado. Proton/Steam para juegos, Wine/Bottles para aplicaciones generales. Probar gráficos/DXVK/VKD3D solo donde apliquen y con GPU/runtime apropiados.
6. **P1: IA como asistencia de compatibilidad.** Explicar diagnóstico, sugerir perfiles probados y ejecutar cambios autorizados con rollback. No permitir que la IA invente compatibilidad ni instale paquetes arbitrarios desde un log.
7. **P2: pulido avanzado y medios.** Voz avanzada, transparencias/dock, TV/radio y otras plataformas siguen registrados, pero no desplazan las pruebas Windows. Seguridad básica y estabilidad acompañan todas las etapas.

## Investigación e ingeniería inversa para interoperabilidad

Estudiar Wine/Proton/Bottles y sus licencias, contratos Win32/Win64, carga PE, instaladores, DLL y dependencias. Usar código abierto y documentación primaria. Diagnosticar ejecutables autorizados mediante imports, trazas de APIs, logs Wine y pruebas mínimas reproducibles; contrastar con comportamiento esperado. Corregir configuraciones o componentes abiertos y aportar parches upstream si corresponde. No copiar código propietario ni eludir licencias, DRM o anticheat. No presentar investigación o diseño como ejecución ya lograda.

Fuentes primarias: https://www.winehq.org/ (la página about devolvió 403 al consultar; no atribuirle lectura), https://github.com/ValveSoftware/Proton (Steam Play basado en Wine), https://docs.usebottles.com/ . Instaladores de referencia: https://www.7-zip.org/ y https://notepad-plus-plus.org/ ; descarga/versión/hash aún pendientes.

## Matriz y criterios de aceptación

Cada caso debe registrar aplicación, versión, arquitectura, origen/hash instalador, licencia/acceso, SHA Nexus, entorno, Wine/runner, prefijo, dependencias, pasos, logs, resultado y limitaciones. Estados: no probado / instala / abre / tarea útil / persiste / aceptado con restricciones / bloqueado.

- Caso base: instalar, ejecutar una función representativa y verificar salida, no solo proceso vivo.
- Caso objetivo del usuario: flujo importante completo y repetible, guardado de datos y reapertura.
- Integración: instalar desde Horizon, ejecutar desde menú, ver diagnóstico, desinstalar sin afectar otro prefijo.
- Persistencia: repetir tras arranque del disco sin ISO.
- Gráficos/juegos: versión y hardware concretos, función sostenida y restricciones registradas; no extrapolar a todos los títulos.

## Estado inicial y medida

Windows: 25 % estimado por investigación/arquitectura y piezas preliminares; **ninguna aplicación Windows está actualmente validada en Nexus según la evidencia disponible**. No subir ese porcentaje por crear este roadmap. Prioridad/peso de Windows pasa a 30 % del global; instalación 15 %. Consultar PROJECT-PROGRESS.md para cálculo completo. El siguiente incremento requiere implementación y pruebas reales, no más documentos.

Dato útil que falta del usuario: aplicación Windows más importante/problemática, versión y tarea que debe funcionar. Mientras se obtiene, puede avanzar el laboratorio base. No bloquear investigación y herramientas por ese dato.
