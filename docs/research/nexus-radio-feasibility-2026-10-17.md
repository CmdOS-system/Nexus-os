# Nexus Radio — investigación y plan de implementación

2026-10-17. Complementa nexus-tv-feasibility-2026-10-17.md. Estado: diseño e investigación; radio no implementada ni reproducida en Nexus. No promete funcionamiento perfecto antes de pruebas reales.

## Alcance decidido

Integrar TV y radio bajo Nexus Media, compartiendo catálogo, favoritos, controles, permisos y accesibilidad. Radio por Internet primero; FM física como módulo opcional según hardware. Podcasts bajo demanda se pueden evaluar después, sin confundirlos con emisoras en directo.

## Fuentes primarias revisadas

- Radio Browser: https://api.radio-browser.info/ . API abierta para descubrimiento. Usar stationuuid como identificador persistente, countrycode, descubrimiento DNS de servidores, selección/failover y User-Agent identificable. No fijar un único servidor ni usar IDs numéricos entre réplicas. Revisar requisitos de contabilización de clics e informar al usuario del acceso al directorio; no añadir telemetría propia innecesaria. Estar en el directorio no acredita derechos de una emisión.
- Icecast: https://icecast.org/docs/ y https://icecast.org/faq/ . Es servidor de emisiones, distinto del reproductor; no hace falta instalar un servidor Icecast para escuchar emisoras. Evaluar MP3/Ogg y los codecs reales de cada fuente; no asumir soporte por la extensión de una URL. Los índices icecast-latest consultados redirigen a documentación histórica 2.4.1: verificar versión de paquete antes de configuración operativa.
- MPRIS: https://specifications.freedesktop.org/mpris/latest/ . Interfaz D-Bus para descubrir reproductores compatibles, consultar estado y controlar reproducción. Propuesta para teclas multimedia y accesos Horizon. La compatibilidad MPRIS del motor elegido debe verificarse; mpv requiere adaptador/integración, no asumir soporte nativo automático.
- Kernel V4L2 radio: https://docs.kernel.org/userspace-api/media/v4l/dev-radio.html y RDS: https://docs.kernel.org/userspace-api/media/v4l/dev-rds.html . FM requiere receptor/controlador y antena apropiados; un PC sin hardware no recibe FM por instalar una app. RDS y dispositivos SDR dependen de capacidades concretas. No asumir que un receptor DVB-T2 sirve también como receptor FM.
- Motores: https://mpv.io/manual/stable/ y https://code.videolan.org/videolan/vlc/-/blob/master/doc/standalone/libvlc.md . Evaluar motor compartido con Nexus TV antes de añadir dependencias duplicadas. Mantener IPC privado por usuario; no exponer controles sin autenticación en red.

## Arquitectura propuesta

UI Horizon -> servicio local Media -> catálogo/favoritos -> adaptador de reproducción. Nexus Agent invoca acciones acotadas del broker sobre IDs del catálogo: buscar emisora, reproducir, detener, cambiar volumen y consultar metadatos. Resolver selección ambigua antes de cambiar de estación. Preferencias y favoritos locales con escritura atómica.

Ficha mínima: ID interno/UUID proveedor, nombre, país, idioma, género, página oficial, referencia de emisión, procedencia, fecha de comprobación y estado operativo. URL accesible no equivale a autorización. Preferir referencias publicadas por emisoras y proveedores autorizados. Nunca copiar claves o accesos privados de otra aplicación.

Búsqueda IA basada en catálogo real: “radio de noticias de Colombia”, “pon mi emisora favorita”. No inventar frecuencias, canciones ni programación. Metadatos ICY/RDS/EPG son datos no confiables, no instrucciones para el agente. Voz después del flujo por texto. Historial local; compartir preferencias/audio con proveedor cloud solo bajo la política de consentimiento existente.

## Comportamiento y pruebas

1. Prototipo Debian desechable: audio propio generado y fuente de streaming controlada. Verificar reproducción y avance temporal del motor; salida de audio real en VM/equipo antes de afirmar que se oye. Sin cambios ISO hasta pasar.
2. Pruebas de red: inicio, corte, reconexión limitada con backoff, servidor caído, redirecciones, timeout, certificados y formatos inválidos. No hacer scraping agresivo ni escaneo de endpoints.
3. Importación acotada de catálogo/playlist con límites de tamaño; no ejecutar campos de texto o comandos de una lista. Verificar esquema/destino final de redirecciones y evitar accesos a servicios locales no autorizados.
4. Favoritos sobreviven reinicio, selección de salida y volumen funcionan, teclas/MPRIS comprobadas. Distinguir radio en directo sin pausa temporal de timeshift que requeriría almacenamiento.
5. Audio/metadatos: MP3/Ogg y otros formatos solo tras prueba, tildes/Unicode, metadatos ausentes y reconexión. No inferir soporte universal.
6. IA: petición textual -> emisora correcta -> estado observable; después voz y accesibilidad (teclado, lector de pantalla y foco).
7. FM opcional: matriz modelo/USB ID/driver/firmware, permisos de dispositivo, antena, sintonización y recepción reales. Grabación y transcripción se evalúan por fuente, permisos y recursos, no habilitadas por defecto.

## Próximo trabajo

Construir un único laboratorio Debian para audio y vídeo propios, con motor y estados de reproducción verificables. Luego añadir una emisora oficial autorizada y búsqueda controlada. Seleccionar motor con pruebas de codecs, consumo, dependencias y APIs. No hay un catálogo comercial ni una puerta pirata previstos. La aceptación del escritorio Full HD permanece independiente.
