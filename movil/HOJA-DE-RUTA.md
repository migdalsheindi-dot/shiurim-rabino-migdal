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
- Borradores de la política de privacidad y de las respuestas de privacidad para las tiendas (carpeta `legal/`).

---

## 2. Decisiones que tienen que tomar ustedes ❓

| # | Qué decidir | Opciones | Mi recomendación |
|---|---|---|---|
| D1 | **Botón "Donar" en la app** | ✅ **Decidido (28/10/2026):** no se muestra en la app hasta que el enlace de Mercado Pago sea de la cuenta de la comunidad. En la web sigue igual | Cuando cambie el enlace, se vuelve a mostrar abriendo la página de pago afuera de la app (lo hace Claude) |
| D2 | **Correo público** para privacidad y para las tiendas | (a) un reenvío gratis en Namecheap, por ejemplo `contacto@yoelmigdal.com`, que llega al correo del Rabino; (b) un Gmail nuevo | **(a)**. Google muestra este correo **públicamente** en la ficha de la app |
| D3 | **¿La app también para iPad?** | ✅ **Decidido (28/10/2026):** sí, iPhone y iPad | Apple pide capturas de iPad (de 13"). El diseño se probó con tamaños de iPad en la computadora |
| D4 | **Nombre en las tiendas** | Por ejemplo "Rabino Yoel Migdal" o "Shiurim – Rabino Yoel Migdal" | Algo corto: en el iPhone se ve "Rabino Yoel Migdal" debajo del ícono |
| D5 | **Países donde se publica** | Todos, o elegir | Todos. Ver el aviso de la Unión Europea en la sección 5 |

---

## 3. Tareas, en orden

### Etapa A — Preparación (se puede hacer ya, sin pagar nada)

1. **Vos:** leer el borrador `legal/politica-de-privacidad.md` y avisarme qué cambiar.
2. **Rabino:** leer la política y aprobarla. Idealmente, que la mire también un abogado.
3. **Vos:** crear el correo público en Namecheap (D2). Pasos: namecheap.com → Domain List → Manage en yoelmigdal.com → Redirect Email → Add Forwarder.
4. **Claude:** poner el correo en la política, armar la página `privacidad.html` de la web y agregar el enlace en el pie de la web y en el menú de la app. Es un cambio en la web: te pido permiso antes.
5. **Vos:** publicar la web con la política. Desde el otro chat, o me pedís permiso a mí.
6. ~~**Claude:** aplicar las decisiones D1 y D3 en la app.~~ Hecho el 28/10/2026.
7. **Juntar 12 personas con teléfono Android** (familia, alumnos, comunidad) que acepten probar la app **14 días seguidos**. Google lo exige para cuentas personales nuevas (ver la sección 5). Conviene empezar a juntarlas ya.

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

11. **Claude:** cambiar la firma de la app de tu cuenta gratuita a la cuenta del Rabino, y armar las versiones finales para iPhone y para Android.
12. **Claude + Vos:** sacar las **capturas de pantalla** (ver la sección 4).
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
| Nombre de la app | máx. 30 caracteres | máx. 30 caracteres | D4 |
| Subtítulo / descripción corta | 30 caracteres | 80 caracteres | Ej.: "Shiurim y clases de Torá" |
| Descripción larga | hasta 4000 caracteres | hasta 4000 | Qué es, qué temas hay, funciones (descargas, guardados, transcripción) |
| Palabras clave | 100 caracteres | — | Torá, Tania, Parashá, jasidut, judaísmo, shiurim… |
| Categoría | Educación (o Libros) | Educación | |
| Precio | Gratis | Gratis | |
| Ícono | 1024×1024 (ya está) | 512×512 (lo genero) | |
| Gráfico destacado | — | 1024×500 | Lo diseño con el logo |
| Capturas iPhone | pantalla de 6,9" | — | Mínimo 1, ideal 3 a 5 |
| Capturas iPad | obligatorias (D3 = sí) | — | Pantalla de 13" |
| Capturas Android | — | mínimo 2 de teléfono | |
| URL de privacidad | obligatoria | obligatoria | `yoelmigdal.com/privacidad.html` (Etapa A) |
| URL de soporte | obligatoria | sitio web | `yoelmigdal.com` |
| Correo de contacto | — | obligatorio y público | D2 |
| Clasificación por edad | cuestionario | cuestionario | Sin violencia, sin apuestas, etc. → apta para todo público |
| Privacidad de datos | "App Privacy" | "Seguridad de los datos" | Respuestas listas en `legal/formularios-tiendas.md` |
| Notas para el revisor (Apple) | recomendado | — | Explicar las funciones propias de la app: descargas sin internet, audio en segundo plano |
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
- **Datos públicos del Rabino:** como las cuentas son personales, las tiendas muestran su **nombre legal**. Google muestra además su **país** y el **correo de desarrollador**.
- **Tu instalación de prueba en el iPhone vence a los 7 días.** Se renueva en un minuto, pidiéndomelo.
- **La web y la app comparten el código.** Lo que se publique en la web desde el otro chat también llega a la app, y viceversa. Hoy hay **4 cambios guardados en esta Mac que todavía no se subieron a GitHub**.

---

## 6. Lo que NUNCA hay que pasar por el chat 🔒

- Contraseñas: Apple, Google, Namecheap, Cloudflare, GitHub.
- Códigos de verificación que llegan por SMS o correo.
- Números de tarjeta o datos bancarios.
- Fotos o números de documentos.
- El correo personal del Rabino (no va en el código).

Todo eso lo escriben ustedes directamente en la página de cada servicio. Yo solo necesito saber
**cuándo** está hecho y, como mucho, datos públicos (por ejemplo, el correo público de la D2).
