# Contexto de la app móvil (para continuar en otro chat)

Proyecto: app iOS y Android del **Rabino Yoel Migdal** (shiurim y clases de Torá), basada en la web https://yoelmigdal.com.
Quien habla es hispanohablante y NO es desarrollador: explicar paso a paso, en español, sin jerga. Pedirle confirmación antes de acciones externas (publicar, pagar, crear cuentas).

## Decisiones ya tomadas (2026-10-26)
- **Tecnología: Capacitor 8** (la web empaquetada + funciones nativas). No React Native.
- **Titular de las cuentas de Apple y Google: el Rabino Yoel Migdal** (persona, no empresa). Tipo de cuenta y papeles fiscales: pendiente de analizar.
- La web existente debe seguir funcionando **exactamente igual y en paralelo**. Este chat trabaja SOLO la app (carpeta `movil/`); no editar la web salvo para lo mínimo que la app necesite, y avisarlo.
- Reglas del proyecto: nada de contraseñas/tokens en el chat (los escribe el usuario en su terminal); el email del Rabino no va en el repo ni en el frontend; mensajes de commit terminan con `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; no afirmar como verificado algo que no se probó.

## Cómo está armado
- Repo: `/Users/sheindimigdal/Desktop/app yoel migdal` (GitHub Pages con dominio propio). Rama `main`.
- La web se edita en `fuente/index.html` y se compila con `cd tools && node build.mjs` (genera `index.html`, `app.js`, `styles.css` en la raíz; no editar esos a mano).
- App: `movil/` (appId `com.yoelmigdal.shiurim`, nombre "Rabino Yoel Migdal"). Flujo: compilar la web → `cd movil && npm run sync` (copia a `www/` con `preparar-www.mjs` y hace `cap sync`).
- En el código de la web, `ES_APP` y `rutaSitio()` detectan que corre dentro de la app y leen datos (data-lite.json, transcripts/, miniaturas, enlaces de compartir) de https://yoelmigdal.com; dentro de la app se desactivan el service worker y el botón "Instalar app".
- Los datos los genera solo un workflow de GitHub (`.github/workflows/sync-spotify.yml`) desde el feed de Spotify; un Worker de Cloudflare (`contador/`) hace estadísticas y suscripciones (D1) y avisa a GitHub cuando hay episodios nuevos.
- iOS usa Swift Package Manager (sin CocoaPods). `ios/App/App/Info.plist` tiene `UIBackgroundModes = audio` y `AppDelegate.swift` fija `AVAudioSession .playback` (verificado en iPhone real el 2026-10-26).

## Entorno de la Mac (ya instalado)
Xcode 27.1 (simulador iOS 27.1: solo existe "iPhone Duo", id `0F76F88C-968E-45BD-85AA-1123D20A3CAE`), Java 21 (brew openjdk@21), Android SDK en `/opt/homebrew/share/android-commandlinetools`, emulador `ry-pixel`, CocoaPods. Variables en `~/.zshrc` (bloque `ry-app-entorno`).
- iOS: `xcodebuild -project movil/ios/App/App.xcodeproj -scheme App -destination "platform=iOS Simulator,id=<id>" -derivedDataPath movil/ios/DerivedData CODE_SIGNING_ALLOWED=NO build`
- Android: `cd movil/android && ./gradlew assembleDebug`; emulador: `emulator -avd ry-pixel -no-window`, instalar con `adb install -r app/build/outputs/apk/debug/app-debug.apk`.

## Estado
- Probado: ambas apps compilan y abren con la home real y datos en vivo; en iOS el audio arranca al tocar "Reproducir".
- Probado en iPhone real (2026-10-26, "iPhone de Sheindi", iPhone 18 Pro, iOS 27.0.1): el audio sigue sonando al salir de la app y con la pantalla bloqueada, y los controles de la pantalla de bloqueo aparecen y funcionan.
- NO probado: audio en Android, push, nada de las tiendas.
- Cuidado: el simulador "iPhone Duo" es raro (indicador en la esquina superior derecha que tapó el botón Donar); no asumir que pasa en un iPhone real.

## Instalar en el iPhone real (cuenta personal gratuita, la instalación dura 7 días)
- Firma con el "Personal Team" del Apple ID cargado en Xcode (`DEVELOPMENT_TEAM = MVK59W9R75` en el pbxproj). Cuando exista la cuenta de desarrollador del Rabino, cambiar el Team por el suyo.
- Ya hecho una vez: iPhone de confianza, Apple ID en Xcode, Modo desarrollador activo y certificado aceptado en Ajustes → General → VPN y gestión de dispositivos.
- Compilar: `xcodebuild -project ios/App/App.xcodeproj -scheme App -destination "platform=iOS,id=00008160-000128EC2063400A" -derivedDataPath ios/DerivedData -allowProvisioningUpdates build`
- Instalar y abrir: `xcrun devicectl device install app --device 00008160-000128EC2063400A ios/DerivedData/Build/Products/Debug-iphoneos/App.app` y `xcrun devicectl device process launch --device 00008160-000128EC2063400A com.yoelmigdal.shiurim`

Lista completa para publicar (decisiones, tareas, datos de las tiendas, cuentas): ver `HOJA-DE-RUTA.md`.

## Pendiente (en este orden, de a un tema por vez, sin saturar)
1. ~~Prueba del audio en segundo plano con un iPhone real~~ (hecho y funcionando, 2026-10-26).
2. ~~Ícono y pantalla de inicio propios~~ (hecho 2026-10-26: el logo de la web, libro con "YM" sobre fondo #211B13). Se regeneran con `npm run iconos` (`generar-iconos.mjs` crea `assets/` desde `../icons/logo-ym.svg` y `@capacitor/assets` hace todos los tamaños; el paso `despues` arregla el fondo del ícono adaptativo de Android). En Android 12+ el fondo oscuro de arranque sale de `windowSplashScreenBackground` en `styles.xml`.
3. Funciones nativas para no ser rechazados por Apple (guía 4.2, "web envuelta"):
   - ~~Descargas para escuchar sin internet~~ (hecho 2026-10-26, en `fuente/index.html`, todo detrás de `ES_APP`: la web no cambia, verificado comparando estilos y texto contra la versión anterior). Usa `@capacitor/filesystem` y `@capacitor/file-transfer` llamados con `window.Capacitor.nativePromise` (la web no empaqueta el JS de Capacitor). Archivos en `LIBRARY_NO_CLOUD/descargas/<id>.<ext>` (sin copia a iCloud); en localStorage `ry_descargas` guarda solo el nombre del archivo (la ruta del contenedor de iOS cambia al actualizar). Botón en la ficha del shiur, sección "Descargas" (menú e inicio) y marca en la portada. Probado: en iPhone real (descarga y escucha en modo avión, OK); descarga con avance y reproducción en el simulador de iOS; en el emulador de Android descarga, reproducción y apertura de la app SIN internet, y borrar.
   - Pendiente: notificaciones push de shiurim nuevos (conectadas a la suscripción); requieren la cuenta paga de Apple del Rabino para probarse en iPhone.
4. Botón "Donar" (Mercado Pago) — EN PAUSA (2026-10-26), se decide más adelante. Hoy sigue visible en la app igual que en la web.
   - Reglas leídas el 2026-10-26 (verificar de nuevo antes de publicar): Apple 3.2.2(iv) permite a entidades benéficas no aprobadas recaudar solo FUERA de la app (Safari/SMS) y con la app gratis; 3.2.1(vi) donar dentro de la app solo para "approved nonprofits" con Apple Pay; si el dinero va a una persona/proyecto (no entidad benéfica) Apple lo trata como propina → compra dentro de la app, y fuera de EE. UU. prohíbe enlaces a otros medios de pago. Google Play: solo las "tax exempt donations" quedan fuera de su sistema de cobro.
   - Según quien maneja el proyecto, las recibe una institución registrada, pero falta confirmar: cuál es, si la cuenta de Mercado Pago está a su nombre y si es sin fines de lucro/exenta. Si se confirma: el botón abre la página de donación en el navegador externo. Si no: ocultar "Donar" solo en la app (`ES_APP`).
5. Textos legales: borradores en `legal/politica-de-privacidad.md` y `legal/formularios-tiendas.md` (2026-10-26), esperando la revisión de quien maneja el proyecto y del Rabino. Faltan: correo para privacidad (no el del Rabino en el código; propuesta: crear en Namecheap, donde está el dominio y ya hay reenvío de correo activo, un reenvío `privacidad@yoelmigdal.com` → correo del Rabino; lo hace quien tenga la cuenta, pendiente), publicarla como `privacidad.html` en la web (cambio en la web: pedir permiso) y enlazarla en el pie de la web y en el menú de la app.
6. Punto 2 del plan: cuentas de desarrollador a nombre del Rabino (Apple Developer ~US$99/año, Google Play ~US$25 único; requisitos fiscales, verificación de identidad, y las pruebas cerradas obligatorias de Google para cuentas personales nuevas) y documentos legales (política de privacidad, términos, manejo de datos de suscripción y estadísticas). **Verificar siempre contra la documentación oficial vigente**, las políticas cambian.
7. Punto 3 del plan: seguridad (HTTPS, tokens, datos de suscriptores, CORS del Worker: ~~agregar `capacitor://localhost` y `https://localhost`~~ hecho y publicado en Cloudflare el 2026-10-26; probado: suscripción desde el iPhone real llega a la lista).
8. Cómo mantener web y app sincronizadas sin duplicar código (ya encaminado: un solo código fuente).
