package com.example.nexus.realapp;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.os.Bundle;
import android.util.Log;
import android.view.View;

public final class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(new RuntimeView(this));
    }

    private static final class RuntimeView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private long frame;

        RuntimeView(MainActivity activity) {
            super(activity);
            setContentDescription("Nexus Android application running on Android Runtime");
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            ++frame;
            canvas.drawColor(0xff0b0f19);
            paint.setColor(0xff00f0ff);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(4f);
            float cx = getWidth() / 2f;
            float cy = getHeight() / 2f;
            canvas.drawCircle(cx, cy - 40, 58 + (frame % 5) * 4, paint);
            paint.setStyle(Paint.Style.FILL);
            paint.setTypeface(Typeface.create("sans-serif", Typeface.BOLD));
            paint.setTextSize(27f);
            canvas.drawText("NEXUS / ANDROID RUNTIME", 30, 70, paint);
            paint.setColor(0xffedf7ff);
            paint.setTextSize(24f);
            canvas.drawText("Real APK code is executing", 30, cy + 70, paint);
            paint.setColor(0xff70f5ff);
            paint.setTypeface(Typeface.create("monospace", Typeface.NORMAL));
            canvas.drawText("Live DEX frame: " + frame, 30, cy + 112, paint);
            Log.i("NexusAndroid", "frame=" + frame);
            postInvalidateDelayed(250);
        }
    }
}
