# Nexus TV — viabilidad y arquitectura propuesta

Fecha: 2026-10-17. Investigación documental; NO hay reproducción ni integración implementada o probada. No modifica la ISO ni sustituye el trabajo del escritorio.

## Decisión propuesta

Crear Nexus TV como módulo opcional del escritorio, reutilizando componentes Linux existentes. Primera entrega: guía y favoritos sobre fuentes autorizadas, reproducción y comandos de IA limitados al catálogo configurado. No desarrollar otro motor de vídeo ni extraer canales o credenciales de aplicaciones comerciales.

## Fuentes de televisión

- Emisiones por Internet: fuentes publicadas o facilitadas por su titular/proveedor con autorización para este uso. Disponibilidad pública de una URL y presencia en una lista no acreditan derechos. Mantener procedencia, términos, territorio y fecha de revisión por fuente.
- TDT de Colombia: estándar DVB-T2, con antena, cobertura y receptor compatible. En un PC requiere sintonizador apropiado y controladores/firmware Linux comprobados; una antena por sí sola no convierte el ordenador en receptor. Pendiente matriz real de dispositivos y pruebas en Nexus. Fuente: https://www.tdtparatodos.tv/preguntas-frecuentes y https://www.tdtparatodos.tv/como-me-conecto .
- Servicios de pago: abrir su web/app oficial con cuenta del usuario. Integración nativa solo si existe SDK/API y permiso del proveedor. Widevine enumera soporte de Chrome Linux, pero no garantiza compatibilidad, resolución ni autorización de todos los servicios en Nexus. No distribuir CDM sin permiso ni implementar evasión de DRM. Fuente: https://developers.google.com/widevine/drm/overview .

## Componentes evaluados

| Componente | Uso propuesto | Evidencia y límite |
| --- | --- | --- |
| Kodi + IPTV Simple | Primera interfaz TV, guía, favoritos y reproducción de listas del proveedor | Proyecto documenta M3U y EPG; instalar un cliente no aporta derechos sobre emisiones. https://github.com/kodi-pvr/pvr.iptvsimple |
| Tvheadend | Backend opcional para DVB-T2/IPTV autorizado, EPG y DVR | Proyecto soporta DVB-T/T2, IPTV y API; requiere hardware o fuente, configuración y pruebas. No arrancar servidor expuesto por defecto. https://github.com/tvheadend/tvheadend y https://docs.tvheadend.org/documentation/development/json-api |
| libmpv/mpv | Alternativa para futura interfaz Horizon propia | IPC JSON permite controlar reproducción. Su manual advierte que IPC no es seguro por sí solo: usar canal local privado por usuario y broker. https://mpv.io/manual/stable/ |
| Navegador oficial del servicio | Contenido de suscripción con DRM | Mantener autenticación y restricciones del proveedor; validar servicio por servicio. No asumir que un WebView equivale a un navegador compatible. |

Elegir Kodi para el primer prototipo reduce trabajo de guía/mando/subtítulos; evaluar libmpv después si los requisitos de identidad Horizon justifican mantener una UI propia. Tvheadend es opcional; no es necesario para cada enlace de vídeo.

## IA integrada

Flujo: intención del usuario -> búsqueda en catálogo/EPG -> selección de ID conocido -> broker Nexus -> adaptador de reproducción. Ejemplos: “abre mi canal de noticias”, “qué documentales hay esta noche”, “activa subtítulos”, “pausa”. La guía debe provenir de datos fechados, no de horarios inventados por el modelo.

Primero conectar controles por texto; voz después de comprobar reproducción. El modelo no genera URLs ejecutables ni comandos shell. Las acciones deben resolver IDs del catálogo autorizado y usar argv/API estructurados. Mantener nombres/EPG como datos no confiables, sin convertir instrucciones dentro de la guía en acciones. Confirmar grabaciones y cambios de suscripción/almacenamiento. Modo local preferido; envío de historial de visualización a nube solo con consentimiento explícito.

Guardar contraseñas/tokens en el almacén de secretos existente, no en M3U, commits o logs. Registrar errores con URLs y cabeceras sensibles redactadas. Catálogo local con proveedor, ID, nombre, referencia de reproducción, procedencia de EPG, territorios y estado de autorización. La IA no debe decidir que una fuente es legítima por estar accesible.

## SuperTV: identificación y alcance

La ficha https://play.google.com/store/apps/details?id=com.supertv.yapp identifica SuperTV de Prime IPTV Premium como reproductor multimedia para Android TV/teléfono/tableta. Existen otras aplicaciones con nombre similar, por ejemplo com.rcmx.supertv. No atribuirles las mismas funciones, propietarios o licencias. No se ha confirmado cuál menciona el usuario; falta enlace o identificador exacto.

La ficha no aporta código fuente, protocolo público ni evidencia de derechos sobre un catálogo. No se descargó APK, no se descompiló ni se realizó ingeniería inversa en esta investigación. No confundir SuperTV con Xuper TV o Magis por semejanza de nombre.

Para interoperabilidad: identificar producto y titular, revisar documentación/API/SDK y condiciones, estudiar interfaz y formatos públicos, y probar únicamente datos/cuentas autorizados. Si se necesita análisis de binario para interoperabilidad, delimitar previamente permiso y restricciones aplicables. No extraer claves, sesiones, endpoints privados o catálogos para saltar controles de acceso. No añadir una puerta de acceso a emisiones sin autorización. Los formatos abiertos se pueden soportar para fuentes legítimas sin suministrar catálogos piratas.

## Hitos de aceptación

1. Prototipo separado de ISO con vídeo propio/de prueba autorizado: abrir, pausar, cambiar canal, audio y subtítulos; guardar versión/runtime/logs.
2. Importación acotada de catálogo y EPG de origen autorizado, secretos protegidos y metadatos con procedencia.
3. IA por texto: petición -> ID correcto -> acción verificable; no resultados inventados ni ejecución arbitraria.
4. Sesión Debian 13: reproducción real, mando/teclado y aceleración de vídeo medida; no concluir por mocks.
5. Opcional DVB-T2: detectar receptor/firmware, escanear y reproducir con antena en cobertura; DVR según derechos/condiciones y espacio disponible.
6. Cada proveedor DRM por separado en vía oficial; documentar restricciones. Después voz, accesibilidad y empaquetado opcional Nexus.

Pendientes: identificar SuperTV exacto, seleccionar una fuente de prueba con derechos documentados, validar disponibilidad de paquetes Debian y licencias de componentes, prototipo reproductor y matriz de aceptación. No se han verificado emisiones comerciales ni licencias de contenido por la mera lectura de documentación.
