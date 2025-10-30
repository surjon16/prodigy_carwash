package com.example.balt_app;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;

import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;


public class MyFirebaseInstanceIDService extends FirebaseMessagingService {

    @Override
    public void onMessageReceived(@NonNull RemoteMessage remoteMessage) {
        super.onMessageReceived(remoteMessage);
        getMessage(remoteMessage.getNotification().getTitle() + " FROM SERVICE", remoteMessage.getNotification().getBody());
    }

    public void getMessage(String title, String body) {

        if(Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel("firebase_notification", "firebase_notification", NotificationManager.IMPORTANCE_DEFAULT);
            NotificationManager manager = getSystemService(NotificationManager.class);
            manager.createNotificationChannel(channel);
        }

        NotificationCompat.Builder nt = new NotificationCompat.Builder(this, "firebase_notification");
        NotificationManagerCompat nm = NotificationManagerCompat.from(this);

        nt.setAutoCancel(true);
        nt.setSmallIcon(R.mipmap.ic_launcher_round);
        nt.setContentTitle(title);
        nt.setContentText(body);

        nm.notify(1, nt.build());

    }


}
