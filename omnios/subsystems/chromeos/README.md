# ChromeOS: extensiones CRX y PWA

## Extensiones `.crx`

OmniLoader reconoce `Cr24` como **candidato CRX**, no como paquete confiable. El formato CRX lleva un encabezado delante del ZIP; el parser futuro debe identificar versión, comprobar con aritmética segura que cada longitud cae dentro del archivo, localizar el ZIP y verificar la firma y el publicador antes de extraer o instalar. Luego debe inspeccionar `manifest.json`, permisos, APIs solicitadas y compatibilidad de manifest version. La firma no sustituye la revisión de permisos ni el aislamiento.

No se ejecutará JavaScript de extensión dentro del kernel. La meta futura es un servicio de usuario de extensión/browser con permisos explícitos. Las APIs de Chrome y ChromeOS no están implementadas, y reconocer CRX no equivale a ejecutar aplicaciones de ChromeOS.

## PWA

Una PWA se obtiene desde una URL/origen web y se identifica por su web app manifest y recursos de la aplicación. No hay una cabecera de ejecutable PWA que deba añadirse al detector de magic bytes. Su instalación requerirá una shell web basada en navegador, que debe proveer DOM, motor JS, Service Workers, red y las Web APIs solicitadas por el sitio. Sin esa shell, OmniKernel no puede ejecutar la PWA directamente.

WebAssembly incrustado en una web puede usar DOM, `fetch`, Canvas o WebGPU: el runtime WASI por sí solo no reemplaza esas APIs. Mantener por separado el runner WASI de usuario y la shell web.

## Referencias

- CRX File component de Chromium: https://chromium.googlesource.com/chromium/src/+/HEAD/components/crx_file/
- Magic del encabezado CRX: https://chromium.googlesource.com/chromium/src/+/HEAD/components/crx_file/crx_file.h
- Formato de manifiesto de extensiones: https://developer.chrome.com/docs/extensions/reference/manifest
- Requisitos del manifiesto PWA: https://developer.chrome.com/docs/lighthouse/pwa/installable-manifest
- Migración de Chrome Apps: https://developer.chrome.com/docs/apps/migration
