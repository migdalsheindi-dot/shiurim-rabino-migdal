package com.yoelmigdal.shiurim;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.support.v4.media.MediaMetadataCompat;
import android.support.v4.media.session.MediaSessionCompat;
import android.support.v4.media.session.PlaybackStateCompat;
import androidx.core.app.NotificationCompat;
import androidx.core.app.ServiceCompat;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * Servicio en primer plano mientras hay un shiur en el reproductor: muestra la notificación con
 * atrasar / reproducir-pausar / adelantar (también en la pantalla de bloqueo) y evita que Android
 * corte el audio en segundo plano para ahorrar batería. El audio en sí lo reproduce la web.
 */
public class ServicioAudio extends Service {

    static final String ACCION_ACTUALIZAR = "com.yoelmigdal.shiurim.ACTUALIZAR";
    private static final String ACCION_BOTON = "com.yoelmigdal.shiurim.BOTON";
    private static final String CANAL = "reproduccion";
    private static final int ID_NOTIFICACION = 1;
    private static final long SALTO_MS = 10_000;

    private static ServicioAudio instancia;

    private MediaSessionCompat sesion;
    private final Handler principal = new Handler(Looper.getMainLooper());
    private String titulo = "";
    private String artista = "";
    private String portadaUrl = "";
    private Bitmap portada;
    private boolean reproduciendo;
    private long posicionMs;
    private long duracionMs;
    private float velocidad = 1f;

    static boolean estaActivo() {
        return instancia != null;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        instancia = this;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel canal = new NotificationChannel(CANAL, "Reproducción", NotificationManager.IMPORTANCE_LOW);
            canal.setDescription("Controles del shiur que se está escuchando");
            canal.setShowBadge(false);
            getSystemService(NotificationManager.class).createNotificationChannel(canal);
        }
        sesion = new MediaSessionCompat(this, "Shiurim");
        sesion.setCallback(new MediaSessionCompat.Callback() {
            @Override public void onPlay() { ControlesAudioPlugin.enviarAccion("play", 0); }
            @Override public void onPause() { ControlesAudioPlugin.enviarAccion("pausa", 0); }
            @Override public void onStop() { ControlesAudioPlugin.enviarAccion("pausa", 0); }
            @Override public void onRewind() { ControlesAudioPlugin.enviarAccion("atrasar", 0); }
            @Override public void onFastForward() { ControlesAudioPlugin.enviarAccion("adelantar", 0); }
            @Override public void onSkipToPrevious() { ControlesAudioPlugin.enviarAccion("atrasar", 0); }
            @Override public void onSkipToNext() { ControlesAudioPlugin.enviarAccion("adelantar", 0); }
            @Override public void onSeekTo(long pos) { ControlesAudioPlugin.enviarAccion("ir", pos / 1000.0); }
        });
        sesion.setActive(true);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACCION_BOTON.equals(intent.getAction())) {
            String tipo = intent.getStringExtra("tipo");
            if ("playpausa".equals(tipo)) tipo = reproduciendo ? "pausa" : "play";
            ControlesAudioPlugin.enviarAccion(tipo, 0);
        } else if (intent != null && ACCION_ACTUALIZAR.equals(intent.getAction())) {
            titulo = texto(intent.getStringExtra("titulo"));
            artista = texto(intent.getStringExtra("artista"));
            reproduciendo = intent.getBooleanExtra("reproduciendo", false);
            posicionMs = (long) (intent.getDoubleExtra("posicion", 0) * 1000);
            duracionMs = (long) (intent.getDoubleExtra("duracion", 0) * 1000);
            velocidad = intent.getFloatExtra("velocidad", 1f);
            String url = texto(intent.getStringExtra("portada"));
            if (!url.equals(portadaUrl)) {
                portadaUrl = url;
                portada = null;
                bajarPortada(url);
            }
        }
        mostrar();
        return START_NOT_STICKY;
    }

    private void mostrar() {
        MediaMetadataCompat.Builder datos = new MediaMetadataCompat.Builder()
            .putString(MediaMetadataCompat.METADATA_KEY_TITLE, titulo)
            .putString(MediaMetadataCompat.METADATA_KEY_ARTIST, artista);
        if (duracionMs > 0) datos.putLong(MediaMetadataCompat.METADATA_KEY_DURATION, duracionMs);
        if (portada != null) datos.putBitmap(MediaMetadataCompat.METADATA_KEY_ALBUM_ART, portada);
        sesion.setMetadata(datos.build());
        sesion.setPlaybackState(new PlaybackStateCompat.Builder()
            .setActions(PlaybackStateCompat.ACTION_PLAY | PlaybackStateCompat.ACTION_PAUSE
                | PlaybackStateCompat.ACTION_PLAY_PAUSE | PlaybackStateCompat.ACTION_SEEK_TO
                | PlaybackStateCompat.ACTION_REWIND | PlaybackStateCompat.ACTION_FAST_FORWARD)
            .setState(reproduciendo ? PlaybackStateCompat.STATE_PLAYING : PlaybackStateCompat.STATE_PAUSED,
                posicionMs, reproduciendo ? velocidad : 0f)
            .build());

        Intent abrir = new Intent(this, MainActivity.class).setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
        Notification n = new NotificationCompat.Builder(this, CANAL)
            .setSmallIcon(R.drawable.ic_notificacion)
            .setContentTitle(titulo)
            .setContentText(artista)
            .setLargeIcon(portada)
            .setContentIntent(PendingIntent.getActivity(this, 0, abrir, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT))
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setOnlyAlertOnce(true)
            .setSilent(true)
            .setOngoing(reproduciendo)
            .addAction(android.R.drawable.ic_media_rew, "Atrasar 10 segundos", boton("atrasar", 1))
            .addAction(reproduciendo ? android.R.drawable.ic_media_pause : android.R.drawable.ic_media_play,
                reproduciendo ? "Pausar" : "Reproducir", boton("playpausa", 2))
            .addAction(android.R.drawable.ic_media_ff, "Adelantar 10 segundos", boton("adelantar", 3))
            .setStyle(new androidx.media.app.NotificationCompat.MediaStyle()
                .setMediaSession(sesion.getSessionToken())
                .setShowActionsInCompactView(0, 1, 2))
            .build();
        ServiceCompat.startForeground(this, ID_NOTIFICACION, n,
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q ? ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK : 0);
    }

    private PendingIntent boton(String tipo, int codigo) {
        Intent i = new Intent(this, ServicioAudio.class).setAction(ACCION_BOTON).putExtra("tipo", tipo);
        return PendingIntent.getService(this, codigo, i, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }

    private void bajarPortada(String url) {
        if (url.isEmpty()) return;
        new Thread(() -> {
            try {
                HttpURLConnection con = (HttpURLConnection) new URL(url).openConnection();
                con.setConnectTimeout(8000);
                con.setReadTimeout(8000);
                try (InputStream in = con.getInputStream()) {
                    Bitmap b = BitmapFactory.decodeStream(in);
                    principal.post(() -> {
                        if (instancia == this && url.equals(portadaUrl) && b != null) {
                            portada = b;
                            mostrar();
                        }
                    });
                }
            } catch (Exception e) {
                // Sin internet o sin portada: la notificación sigue sin imagen
            }
        }).start();
    }

    private static String texto(String s) {
        return s == null ? "" : s;
    }

    @Override
    public void onTaskRemoved(Intent rootIntent) {
        // Si la persona cierra la app desde "recientes", se va también la notificación
        stopSelf();
    }

    @Override
    public void onDestroy() {
        instancia = null;
        ServiceCompat.stopForeground(this, ServiceCompat.STOP_FOREGROUND_REMOVE);
        sesion.setActive(false);
        sesion.release();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
