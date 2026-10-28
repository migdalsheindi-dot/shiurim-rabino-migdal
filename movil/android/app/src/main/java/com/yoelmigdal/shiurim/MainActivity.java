package com.yoelmigdal.shiurim;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        // Pieza propia de la app (no viene de npm): controles de reproducción en la notificación
        registerPlugin(ControlesAudioPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
