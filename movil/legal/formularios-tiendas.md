# Respuestas para los formularios de privacidad de las tiendas

Preparado el 26 de octubre de 2026, según cómo funcionan hoy la web y la app y las páginas oficiales:
- Apple, "App privacy details": https://developer.apple.com/app-store/app-privacy-details/
- Google Play, "Data safety": https://support.google.com/googleplay/android-developer/answer/10787469

Antes de enviar la app, revisar de nuevo: las tiendas cambian sus formularios, y estas respuestas
dejan de ser válidas si la app empieza a usar datos nuevos (por ejemplo, avisos push).

Ambas tiendas piden el **enlace público a la política de privacidad**. La propuesta es publicarla en
`https://yoelmigdal.com/privacidad.html` (ver `politica-de-privacidad.md`).

## Apple — App Store Connect → "App Privacy"

**¿La app o sus socios recopilan datos?** Sí.

| Dato (categoría de Apple) | Para qué | ¿Vinculado a la persona? | ¿Rastreo (tracking)? |
|---|---|---|---|
| Contact Info → **Name** | Developer's Advertising or Marketing (novedades por correo) | Sí | No |
| Contact Info → **Email Address** | Developer's Advertising or Marketing | Sí | No |
| Usage Data → **Product Interaction** (visitas, reproducciones, segundos escuchados) | Analytics | No | No |
| Location → **Coarse Location** (solo el país, como contador) | Analytics | No | No |
| Identifiers → **Device ID** (identificador de Firebase para los avisos, solo si los activa) | App Functionality | No | No |

Notas:
- Nombre y email salen del formulario de **Suscripción**. El formulario de **Contacto** usa los mismos datos, así que ya quedan declarados.
- Lo que queda solo en el teléfono (guardados, progreso, descargas) **no se declara**: Apple no lo considera "recopilado".
- **No** hay cuentas, publicidad, venta de datos ni rastreo. No hace falta el aviso de "App Tracking Transparency".

## Google Play — Play Console → "Data safety"

- **¿Recopila o comparte datos?** Sí, los recopila. **No los comparte**: EmailJS y Cloudflare son proveedores que trabajan por cuenta nuestra.
- **¿Están cifrados en tránsito?** Sí (HTTPS).
- **¿Se puede pedir que se borren?** Sí, escribiendo desde Contacto o a consultas@yoelmigdal.com. Hace falta poner un enlace a una página que explique cómo pedirlo; puede ser la misma política, punto 5.

| Tipo de dato (Google) | ¿Obligatorio u opcional? | Para qué |
|---|---|---|
| Personal info → **Name** | Opcional | Developer communications |
| Personal info → **Email address** | Opcional | Developer communications |
| App activity → **App interactions** | Se recopila automáticamente | Analytics |
| Location → **Approximate location** (país) | Se recopila automáticamente | Analytics |
| Device or other IDs → **Device or other IDs** (Firebase, avisos) | Opcional (solo si activa los avisos) | App functionality |

## Pendientes antes de enviar

1. Publicar la política en la web (`privacidad.html`) y poner un enlace en el pie de la web y en el menú de la app.
2. ~~Definir el correo de contacto~~: **consultas@yoelmigdal.com** (reenvío de Namecheap al correo del Rabino; las respuestas salen desde esa misma dirección a través de Resend).
3. ~~Avisos push~~: ya declarados arriba (Device ID / Device or other IDs). En iPhone, cuando se activen, revisar que el manifiesto de privacidad siga siendo correcto.
