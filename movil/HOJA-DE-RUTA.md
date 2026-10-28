# Hoja de ruta de la app del Rabino Yoel Migdal

Todo lo que falta para publicar la app en el App Store (iPhone) y en Google Play (Android): qué hay que
hacer, qué hay que decidir, qué datos hay que cargar y qué conviene saber.

Actualizado: 28 de octubre de 2026. Los requisitos de Apple y Google se leyeron ese día en sus páginas
oficiales, pero **cambian seguido**: hay que volver a revisarlos justo antes de crear las cuentas y de enviar la app.

Quién hace cada cosa: **Vos** = quien maneja el proyecto · **Rabino** · **Claude** = yo, en el chat.

---

## 1. Lo que ya está hecho ✅

- App para iPhone y Android, armada con la misma web (todo lo nuevo de la web aparece solo en la app).
- Audio en segundo plano y controles en la pantalla bloqueada. Probado en tu iPhone.
- Ícono y pantalla de inicio con el logo de la web.
- Descargas para escuchar sin internet. Probado en tu iPhone, en modo avión.
- Suscripción y estadísticas funcionando desde la app. Probado en tu iPhone.
- Política de privacidad revisada (falta la aprobación del Rabino), con enlace en el menú de la app. Respuestas de privacidad para las tiendas listas (carpeta `legal/`).
- Correo público **consultas@yoelmigdal.com**: recibe y puede responder sin mostrar el Gmail del Rabino.
- Textos de las fichas de las tiendas revisados (`tiendas/textos.md`) y todas las imágenes: capturas de iPhone, iPad y Android, gráfico e ícono de Google (`tiendas/imagenes/`).
- "Donar" oculto en la app hasta que el enlace sea de la comunidad. App para iPhone y iPad.
- Android: notificación con controles de reproducción (pausa, adelantar, atrasar, portada) y botón "atrás" que cierra ventanas y vuelve al inicio sin cerrar la app. Probado en el emulador.
- Requisitos técnicos de Apple (manifiesto de privacidad) y firma de Android para Google Play, listos.
- Las notas internas ya no se ven públicamente en yoelmigdal.com.

---

## 2. Decisiones que tienen que tomar ustedes ❓

| # | Qué decidir | Opciones | Mi recomendación |
|---|---|---|---|
| D1 | **Botón "Donar" en la app** | ✅ **Decidido (28/10/2026):** no se muestra en la app hasta que el enlace de Mercado Pago sea de la cuenta de la comunidad. En la web sigue igual | Cuando cambie el enlace, se vuelve a mostrar abriendo la página de pago afuera de la app (lo hace Claude) |
| D2 | **Correo público** para privacidad y para las tiendas | ✅ **Decidido y creado (28/10/2026):** **consultas@yoelmigdal.com**. Reenvío gratis en Namecheap al Gmail del Rabino; las respuestas salen como consultas@ a través de Resend (gratis, 100 correos/día) | Falta configurar "Enviar como" en el Gmail del Rabino |
| D3 | **¿La app también para iPad?** | ✅ **Decidido (28/10/2026):** sí, iPhone y iPad | Apple pide capturas de iPad (de 13"). El diseño se probó con tamaños de iPad en la computadora |
| D4 | **Nombre en las tiendas** | ✅ **Decidido (28/10/2026):** "Rabino Yoel Migdal – Shiurim" | Debajo del ícono se ve "Rabino Yoel Migdal" |
| D5 | **Países donde se publica** | Todos, o elegir | Todos. Ver el aviso de la Unión Europea en la sección 5 |

---

## 3. Tareas, en orden

### Etapa A — Preparación (se puede hacer ya, sin pagar nada)

1. ~~**Vos:** revisar el borrador de la política.~~ Hecho el 28/10/2026; PDF enviado al Rabino (`legal/Politica-de-privacidad-Rabino-Yoel-Migdal.pdf`).
2. **Rabino:** leer la política y aprobarla. Puntos ya confirmados (28/10/2026): domicilio solo "CABA", formularios para mayores de 13, la suscripción sirve para novedades del Rabino y de sus actividades (sin nombrar a ISEJ), la baja se pide a consultas@. Pendiente: que la lea alguien con conocimiento legal del entorno del Rabino o de ISEJ.
3. ~~**Vos:** crear el correo público (D2).~~ Hecho el 28/10/2026: consultas@yoelmigdal.com.
4. ~~**Claude:** armar la página de privacidad y el enlace en el menú de la app.~~ Hecho el 28/10/2026: el enlace "Política de privacidad" ya está en el menú de la app (solo en la app). La página se genera con `node movil/legal/generar-privacidad.mjs` (crea `privacidad.html` en la raíz) **recién cuando el Rabino apruebe la política**, y se publica con la web.
5. **Vos:** publicar la web con la política. Desde el otro chat, o me pedís permiso a mí.
6. ~~**Claude:** aplicar las decisiones D1 y D3 en la app.~~ Hecho el 28/10/2026.
7. **Juntar 12 personas con teléfono Android** (familia, alumnos, comunidad) que acepten probar la app **14 días seguidos**. Google lo exige para cuentas personales nuevas (ver la sección 5). Conviene empezar a juntarlas ya.

3b. **Rabino — responder como consultas@yoelmigdal.com** (en Gmail **de computadora**, no en la app del celular):
    - Antes: pedirle a quien maneja el proyecto la clave de Resend (empieza con `re_`); no se manda por chat.
    - Gmail → ⚙️ → Ver toda la configuración → **Cuentas e importación** → "Enviar como" → **Agregar otra dirección**.
    - Nombre: `Rabino Yoel Migdal` · Dirección: `consultas@yoelmigdal.com` · Siguiente.
    - Servidor SMTP `smtp.resend.com` · Puerto `587` · Usuario `resend` · Contraseña: la clave `re_…` · Conexión segura con TLS → Agregar cuenta.
    - Confirmar con el correo que llega a consultas@ (cae en su mismo Gmail).
    - En "Al responder a un mensaje" elegir **"Responder desde la misma dirección a la que se envió el mensaje"**.

### Etapa B — Cuentas de desarrollador (las hace el Rabino, con sus datos)

8. **Rabino — Apple Developer Program** (developer.apple.com/programs/enroll):
   - Necesita un **Apple ID** (su cuenta de iCloud) con **verificación en dos pasos** activada.
   - El nombre y el apellido del Apple ID tienen que ser su **nombre legal real**, sin apodos. Si no coinciden, la aprobación se demora.
   - Pide **dirección, teléfono y correo**. No aceptan casillas de correo postal.
   - Cuesta **US$ 99 por año**. Se paga en moneda local con tarjeta.
   - **En la tienda va a figurar su nombre legal como vendedor.**
   - Puede pedir que verifique su identidad con un documento, por ejemplo desde la app "Apple Developer".
9. **Rabino — Google Play Console** (play.google.com/console), cuenta **personal**:
   - Necesita una **cuenta de Google**.
   - Cuesta **US$ 25, un solo pago**.
   - Su **nombre legal y su dirección** salen de su perfil de pagos de Google. Hay que **verificar su identidad**, con documento.
   - Hay que verificar el **correo y el teléfono de contacto** con un código.
   - **En Google Play se muestran públicamente:** el nombre de desarrollador (puede ser "Rabino Yoel Migdal"), su **nombre legal**, su **país** y el **correo de desarrollador**. Por eso conviene el correo de D2.
   - Es probable que pida comprobar que tiene un **teléfono Android real**, desde la app Play Console. Esto lo tengo que confirmar en el momento.
10. **Rabino → Vos:** una vez aprobadas, que te sume como **usuario/administrador** en las dos cuentas. Así no hace falta compartir contraseñas:
    - Apple: App Store Connect → Usuarios y acceso.
    - Google: Play Console → Usuarios y permisos.

### Etapa C — Armar y probar las versiones para las tiendas

- Ya hecho (28/10/2026): manifiesto de privacidad de Apple, firma de Android lista (llave en `~/claves-app-yoel-migdal`, **hacer copia**), versión de Google Play compilada y firmada.
- Hecho (28/10/2026): notificación con controles de reproducción en Android, probada en el emulador. Falta probarla en un Android real (puede ser uno de los 12 testers).
- Al cargar la app en Google Play: declarar el uso de "servicio en primer plano de reproducción multimedia" (Play Console lo pide; suele requerir un video corto mostrando la notificación). Lo preparo yo.

11. **Claude:** cambiar la firma de la app de tu cuenta gratuita a la cuenta del Rabino, y armar las versiones finales para iPhone y para Android.
12. ~~**Claude:** sacar las **capturas de pantalla** y el gráfico de Google (ver la sección 4).~~ Hecho el 28/10/2026, en `tiendas/imagenes/` (4 de iPhone 1320×2868, 4 de iPad 2064×2752, 4 de Android 1080×2160, gráfico 1024×500 e ícono 512×512). Si cambia el diseño de la app, hay que volver a sacarlas.
13. **Vos:** cargar la ficha de la app en cada tienda con los datos de la sección 4. Yo te dicto qué va en cada campo.
14. **Google:** subir la app a **prueba cerrada**, invitar a las 12 personas y esperar **14 días seguidos**. Ninguna puede salirse antes.
15. **Apple:** subir la app a **TestFlight**, la prueba de Apple, y probarla en tu iPhone.

### Etapa D — Enviar a revisión y publicar

16. **Apple:** enviar a revisión. Suele tardar entre 1 y 3 días. Si la rechazan, explican el motivo y se corrige.
17. **Google:** después de los 14 días, tocar **"Solicitar acceso a producción"** y contestar las preguntas sobre la prueba. Google tarda **hasta 7 días** o más. Después se envía la versión final, que también se revisa.
18. **Publicar.** Apple: se puede elegir publicarla apenas la aprueben, o a mano.

### Después de publicar

19. **Claude:** avisos de shiurim nuevos (notificaciones). Necesitan la cuenta paga de Apple para poder probarse.
20. **Rabino:** renovar Apple cada año (US$ 99). Si no se paga, la app desaparece del App Store.
21. **Cada tanto:** las tiendas piden actualizar la app a versiones nuevas de iOS/Android, más o menos una vez por año. Los shiurim nuevos **no** necesitan actualizar la app: aparecen solos.

---

## 4. Datos que hay que cargar en las tiendas 📝

Yo puedo redactar los textos. Ustedes los revisan.

| Dato | Apple | Google | Comentario |
|---|---|---|---|
| Nombre de la app | máx. 30 caracteres | máx. 30 caracteres | ✅ "Rabino Yoel Migdal – Shiurim" |
| Subtítulo / descripción corta | 30 caracteres | 80 caracteres | ✅ Listos en `tiendas/textos.md` |
| Descripción larga | hasta 4000 caracteres | hasta 4000 | ✅ Lista en `tiendas/textos.md` |
| Palabras clave | 100 caracteres | — | ✅ Listas en `tiendas/textos.md` |
| Categoría | ✅ Educación + Libros | ✅ Educación | |
| Precio | Gratis | Gratis | |
| Ícono | ✅ 1024×1024 | ✅ 512×512 | `tiendas/imagenes/google/` |
| Gráfico destacado | — | ✅ 1024×500 | `tiendas/imagenes/google/` |
| Capturas iPhone | ✅ 4, pantalla de 6,9" | — | `tiendas/imagenes/iphone/` |
| Capturas iPad | ✅ 4, pantalla de 13" | — | `tiendas/imagenes/ipad/` |
| Capturas Android | — | ✅ 4 de teléfono | `tiendas/imagenes/android/` |
| URL de privacidad | obligatoria | obligatoria | `yoelmigdal.com/privacidad.html` (se publica cuando el Rabino apruebe) |
| URL de soporte | obligatoria | sitio web | `yoelmigdal.com` |
| Correo de contacto | — | obligatorio y público | ✅ consultas@yoelmigdal.com |
| Clasificación por edad | cuestionario | cuestionario | Sin violencia, sin apuestas, etc. → apta para todo público |
| Privacidad de datos | "App Privacy" | "Seguridad de los datos" | ✅ Respuestas listas en `legal/formularios-tiendas.md` |
| Notas para el revisor (Apple) | recomendado | — | ✅ Listas en `tiendas/textos.md` |
| ¿Tiene anuncios? | — | No | |
| Público objetivo | — | 13 años o más | Coherente con la política |
| Usuario y contraseña de prueba | no hace falta | no hace falta | La app no tiene cuentas |

---

## 5. Lo que conviene saber ⚠️

- **Costos:** Apple US$ 99/año + Google US$ 25 una sola vez. El resto es gratis: el servidor de estadísticas, la web y estas herramientas.
- **Tiempos aproximados:** aprobación de las cuentas, de 1 día a 2 semanas · prueba de Google, 14 días como mínimo + hasta 7 de revisión · revisión de Apple, de 1 a 3 días por envío.
- **El riesgo más grande con Apple** es que diga que la app es "solo una página web" (regla 4.2). Para eso agregamos funciones propias: descargas sin internet y audio en segundo plano. Después vendrán los avisos. **Nadie puede garantizar la aprobación**: si la rechazan, se corrige y se vuelve a enviar.
- **Donaciones:** ver D1. Apple no permite pagar o donar por fuera de la app salvo a instituciones benéficas, y siempre abriendo afuera de la app. Google solo exceptúa las donaciones exentas de impuestos.
- **Unión Europea:** Apple pide declarar si el desarrollador es "comerciante" (trader). Si lo es, muestra su dirección y teléfono. Para una app gratuita sin fines comerciales se suele declarar "no comerciante", pero hay que confirmarlo en el momento. También se puede no publicarla en la Unión Europea.
- **Avisos para Google Play:** declarar "servicio en primer plano de reproducción multimedia" (por la notificación de Android; suele pedir un video corto) y probar en un Android real.
- **Llave de Android:** la carpeta `claves-app-yoel-migdal` (en tu carpeta personal) y su clave **no se pueden perder**: guardá una copia.
- **El repositorio de GitHub es público:** nunca poner ahí contraseñas, claves ni datos personales.
- **Datos públicos del Rabino:** como las cuentas son personales, las tiendas muestran su **nombre legal**. Google muestra además su **país** y el **correo de desarrollador**.
- **Tu instalación de prueba en el iPhone vence a los 7 días** (la última, el 4/11/2026). Se renueva en un minuto, pidiéndomelo.
- **La web y la app comparten el código.** Lo que se publique en la web desde el otro chat también llega a la app, y viceversa. Los cambios de la app se guardan en esta Mac y se suben con la próxima publicación de la web; ninguno cambia lo que se ve en la web.

---

## 6. Lo que NUNCA hay que pasar por el chat 🔒

- Contraseñas: Apple, Google, Namecheap, Cloudflare, GitHub.
- Códigos de verificación que llegan por SMS o correo.
- Números de tarjeta o datos bancarios.
- Fotos o números de documentos.
- El correo personal del Rabino (no va en el código).

Todo eso lo escriben ustedes directamente en la página de cada servicio. Yo solo necesito saber
**cuándo** está hecho y, como mucho, datos públicos (por ejemplo, el correo público de la D2).
