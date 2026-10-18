# Word y Office de escritorio: criterio principal Windows

Corte: 2026-10-17 Bogotá. Requisito explícito del usuario: demostrar compatibilidad instalando una aplicación como Word/Office.7-Zip y Notepad++ son pruebas básicas del motor, no sustituyen esta aceptación. **Word todavía no está validado en Nexus.**

## Investigación primaria y decisión

- [Microsoft: Office Deployment Tool](https://learn.microsoft.com/en-us/microsoft-365-apps/deploy/overview-office-deployment-tool): setup.exe y XML; /download prepara archivos, /configure instala. Descargar ODT no equivale a instalar Office.
- [Microsoft: opciones de configuración](https://learn.microsoft.com/en-us/microsoft-365-apps/deploy/office-deployment-tool-configuration-options): producto, arquitectura, canal, idioma, exclusión de apps y presentación del instalador. No mezclar arquitecturas de Office en un mismo perfil.
- [Descarga oficial ODT](https://www.microsoft.com/en-us/download/details.aspx?id=49117): versión16.0.20326.20112, publicada09/09/2026; sistemas Windows enumerados. Linux/Wine no aparecen como plataforma soportada por Microsoft en esa página.
- [Guía Linux de CodeWeavers](https://support.codeweavers.com/en_US/user-guides/crossover-linux-user-guide): botellas, recetas y dependencias. Es una ruta a evaluar; no demuestra que el paquete actual de Microsoft365 funcione con Wine Debian ni autoriza redistribuir CrossOver.
- [WinApps, mecanismo](https://github.com/winapps-org/winapps): aplicaciones ejecutadas en Windows virtualizado y presentadas con FreeRDP; soporta escritorio XFCE. [Preparación de VM](https://github.com/winapps-org/winapps/blob/main/docs/docker.md) requiere edición Windows apropiada para RDP, KVM y recursos. Es backend diferente de Wine, no implementación Win32 nativa ni garantía universal.

Primero realizar un intento acotado y reproducible del instalador actual de Microsoft bajo Wine. Si falla, registrar fase, código y pantalla; no repetir indefinidamente con más tiempo ni afirmar soporte de Office por usar versiones antiguas. Evaluar CrossOver por versión exacta y WindowsVM/RemoteApp como segunda ruta. Una eventual VM debe quedar expresamente identificada en interfaz/documentación, requerir permisos/recursos adecuados y licencias correspondientes; ninguna ruta está aceptada hoy.

## Instalador fijado y laboratorio inicial

URL: https://download.microsoft.com/download/6c1eeb25-cf8b-41d9-8d0d-cc1dbc032140/officedeploymenttool_20326-20112.exe

SHA256 descargado directamente del enlace de Microsoft: `fbb64358fd4168acd52ee4efe47ffd032b6231dfb415ae2dce61b0e58ba67f86`. PE32 confirmado localmente; no es firma de aceptación de Office.

`agent/tests/windows_office_lab.py` intenta extraer ODT, inicializar perfil Wine64+32 aislado e instalar Word del producto Microsoft365 Apps for enterprise32bit/en-us/Current. Registra versiónODT y hashsetup/Word si existen. El canal puede cambiar: el resultado solo vale para el binario concretamente registrado; no es fijación del buildOffice por nombre de canal. Otros programas de Office se excluyen en este primer caso para centrar la tarea en Word.

Después intenta abrir DOCX sintético, editar por teclado, guardar, validar contenido OOXML, reiniciar Wine y reabrir el mismo documento. Falla si la instalación, activación, render o diálogo impiden la tarea. Artefactos contienen resultadoJSON, logs y capturas; no instaladores, perfiles completos, claves ni credenciales. No se elude activación ni se crea suscripción. Una barrera de licencia se registra como bloqueo y exige el flujo legítimo del usuario. El laboratorio no incorpora Office al catálogo aprobado del instalador Nexus.

## Aceptación dentro de Nexus: siete requisitos, todos pendientes

| Requisito | Evidencia exigida | Estado |
| --- | --- | --- |
| 1. Instalación | Instalador oficial, versión/canal/arquitectura y hash; registro de instalación real | Pendiente |
| 2. Apertura | WINWORD.EXE y ventana de escritorio real, sin editor negro ni pantalla web | Pendiente |
| 3. Documento útil | AbrirDOCX con tildes, tabla e imagen; editar texto y formato | Pendiente |
| 4. Guardar/reabrir | DOCX guardado por Word con contenido correcto y abierto tras cerrarWord/motor | Pendiente |
| 5. Salida | ExportarPDF y revisar páginas, tabla, imagen y caracteres | Pendiente |
| 6. Integración | MenúHorizon, abrirDOCX desdearchivos, errores claros y flujo sinterminal | Pendiente |
| 7. Persistencia | Nexusinstalado enQCOW2; reinicio sinISO conservaWord/documentos y vuelveaabrir | Pendiente |

Aprobación de laboratorio representa solo base técnica. Word web, LibreOffice o un visorDOCX no satisfacen esta prueba de WordWindows. No generalizar un resultadoWord a Excel/PowerPoint/Outlook, macros, plugins, impresión o todas las versionesOffice. Registrar esos casos por separado. No subirWindows de50% a75% solo por la instalación o un único caso; evaluar la amplitud del módulo y los criterios completos.

## Siguiente entrega

1. Revisar el primer run del laboratorioOffice y sus artefactos antes de modificar runtime.
2. Resolver el primer bloqueo reproducible o decidir backend alternativo con evidencia.
3. Integrar en Nexus el backend que funcione y repetir los siete requisitos arriba.
4. MantenerOffice como P0 funcional de compatibilidad; APK/Linux siguen en alcance sin porcentaje ficticio.
