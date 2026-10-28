package com.yoelmigdal.shiurim;

import android.content.Intent;
import androidx.core.content.ContextCompat;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * Puente entre el reproductor de la web (fuente/index.html) y ServicioAudio: la web avisa qué suena
 * ("actualizar") y cuándo se cierra el reproductor ("detener"); los botones de la notificación, de la
 * pantalla de bloqueo y de los auriculares vuelven a la web como el evento "accion".
 */
@CapacitorPlugin(name = "ControlesAudio")
public class ControlesAudioPlugin extends Plugin {

    private static ControlesAudioPlugin instancia;

    @Override
    public void load() {
        instancia = this;
    }

    @PluginMethod
    public void actualizar(PluginCall call) {
        Intent i = new Intent(getContext(), ServicioAudio.class);
        i.setAction(ServicioAudio.ACCION_ACTUALIZAR);
        i.putExtra("titulo", call.getString("titulo", ""));
        i.putExtra("artista", call.getString("artista", ""));
        i.putExtra("portada", call.getString("portada", ""));
        i.putExtra("reproduciendo", Boolean.TRUE.equals(call.getBoolean("reproduciendo", false)));
        i.putExtra("posicion", call.getDouble("posicion", 0.0));
        i.putExtra("duracion", call.getDouble("duracion", 0.0));
        i.putExtra("velocidad", call.getFloat("velocidad", 1f));
        if (ServicioAudio.estaActivo()) {
            // Ya corre en primer plano: alcanza con pasarle los datos nuevos
            getContext().startService(i);
        } else {
            ContextCompat.startForegroundService(getContext(), i);
        }
        call.resolve();
    }

    @PluginMethod
    public void detener(PluginCall call) {
        getContext().stopService(new Intent(getContext(), ServicioAudio.class));
        call.resolve();
    }

    /** tipo: "play", "pausa", "atrasar", "adelantar" o "ir" (con posicion en segundos). */
    static void enviarAccion(String tipo, double posicion) {
        if (instancia == null) return;
        JSObject datos = new JSObject();
        datos.put("tipo", tipo);
        datos.put("posicion", posicion);
        instancia.notifyListeners("accion", datos);
    }
}
