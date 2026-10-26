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
- La web se edita en `fuente/index.html` y se compila con `cd tools && npm run build` (genera `index.html`, `app.js`, `styles.css` en la raíz; no editar esos a mano).
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

## Pendiente (en este orden, de a un tema por vez, sin saturar)
1. ~~Prueba del audio en segundo plano con un iPhone real~~ (hecho y funcionando, 2026-10-26).
2. Ícono y pantalla de inicio propios (hoy son los genéricos de Capacitor).
3. Funciones nativas para no ser rechazados por Apple (guía 4.2, "web envuelta"): notificaciones push de shiurim nuevos (conectadas a la suscripción), descargas para escuchar sin internet.
4. Botón "Donar" (Mercado Pago): tiene reglas específicas de Apple para donaciones; analizar y decidir (puede ir por Safari o ocultarse en iOS).
5. Punto 2 del plan: cuentas de desarrollador a nombre del Rabino (Apple Developer ~US$99/año, Google Play ~US$25 único; requisitos fiscales, verificación de identidad, y las pruebas cerradas obligatorias de Google para cuentas personales nuevas) y documentos legales (política de privacidad, términos, manejo de datos de suscripción y estadísticas). **Verificar siempre contra la documentación oficial vigente**, las políticas cambian.
6. Punto 3 del plan: seguridad (HTTPS, tokens, datos de suscriptores, CORS del Worker: agregar `capacitor://localhost` y `https://localhost` solo cuando la app los necesite).
7. Cómo mantener web y app sincronizadas sin duplicar código (ya encaminado: un solo código fuente).
