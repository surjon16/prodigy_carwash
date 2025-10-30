package com.example.balt_app;

import androidx.annotation.RequiresApi;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;

import android.annotation.SuppressLint;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.graphics.Bitmap;
import android.media.MediaPlayer;
import android.os.AsyncTask;
import android.os.Build;
import android.os.Bundle;

import android.os.Handler;
import android.view.View;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.Timer;
import java.util.TimerTask;

public class MainActivity extends AppCompatActivity {

    String url = "https://vincentcubillan.pythonanywhere.com";
//    String url = "http://192.168.110.108:8080";

    NotificationCompat.Builder nt;
    NotificationManagerCompat nmc;

    private WebView webView;
    private static final int ntID = 36900;

    MediaPlayer mp;
    String JSON_STRING;


    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        if(Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel("localnotif", "localnotif", NotificationManager.IMPORTANCE_DEFAULT);
            NotificationManager manager = getSystemService(NotificationManager.class);
            manager.createNotificationChannel(channel);
        }

        webView=(WebView) findViewById(R.id.webview);
        webView.setWebViewClient(new WebViewClient());
        webView.getSettings().setJavaScriptEnabled(true);
        webView.setFocusable(true);
        webView.setFocusableInTouchMode(true);
        webView.getSettings().setCacheMode(WebSettings.LOAD_DEFAULT);
        webView.getSettings().setDomStorageEnabled(true);
        webView.getSettings().setDatabaseEnabled(true);
        webView.getSettings().setAppCacheEnabled(true);
        webView.setScrollBarStyle(View.SCROLLBARS_INSIDE_OVERLAY);
        webView.loadUrl(url + "/member/dashboard");

//        new JsonTask().execute();
//        final Handler handler = new Handler();
//        Timer timer = new Timer();
//        TimerTask doAsynchronousTask = new TimerTask()
//        {
//            @Override
//            public void run() {
//                handler.post(new Runnable() {
//                    public void run() {
//                        try
//                        {
//                            new JsonTask().execute();
//                        }
//                        catch (Exception e){
//                            e.printStackTrace();
//                        }
//                    }
//                });
//            }
//        };
//        timer.schedule(doAsynchronousTask, 0, 1000 * 60); // notify every 1 minute

    }

    public class webClient extends WebViewClient{
        @Override
        public void onPageStarted(WebView view, String url, Bitmap favicon){
            super.onPageStarted(view, url, favicon);
        }
        @Override
        public boolean shouldOverrideUrlLoading(WebView view, String url){
            view.loadUrl(url);
            return true;
        }
    }
//    @Override
//    public void onBackPressed(){
//        if(webView.canGoBack()) {
//            webView.goBack();
//        }
//        else{
//            super.onBackPressed();
//        }
//    }

    class JsonTask extends AsyncTask<Void, Void, String> {

        String dataUrl;

        @Override
        protected void onPreExecute() {
            dataUrl = url + "/api/member/notifications";
        }

        @Override
        protected String doInBackground(Void... params) {
            try {

                URL url = new URL(dataUrl);
                HttpURLConnection httpURLConnection = (HttpURLConnection) url.openConnection();
                InputStream inputStream = httpURLConnection.getInputStream();
                BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(inputStream));
                StringBuilder stringBuilder = new StringBuilder();

                while ((JSON_STRING = bufferedReader.readLine()) != null) {
                    stringBuilder.append(JSON_STRING + "\n");
                }

                bufferedReader.close();
                inputStream.close();
                httpURLConnection.disconnect();

                return stringBuilder.toString().trim();


            } catch (MalformedURLException e) {
                e.printStackTrace();
            } catch (IOException e) {
                e.printStackTrace();
            }

            return null;

        }

        @Override
        protected void onProgressUpdate(Void... values) {
            super.onProgressUpdate(values);
        }

        @RequiresApi(api = Build.VERSION_CODES.M)
        @Override
        protected void onPostExecute(String jsonStr) {

            if (jsonStr != null) {
                try {

                    JSONArray dataArray = new JSONArray(jsonStr);

                    String notifMessage = "";

//                    for (int i = 0; i < dataArray.length(); i++) {
//                        JSONObject b = dataArray.getJSONObject(i);
//                        Double level = b.getDouble("level");
//                        if (level >= 80.0) {
//                            notifMessage += "Bin " + b.getString("dataID") + " is already " + String.format("%.2f", level) + "% full! \n";
//                        }
//                    }


                    if (dataArray.length() > 0 ){

                        nt = new NotificationCompat.Builder(MainActivity.this, "localnotif");
                        nmc = NotificationManagerCompat.from(MainActivity.this);

                        nt.setAutoCancel(true);
                        nt.setSmallIcon(R.mipmap.ic_launcher_round);
                        nt.setTicker("notifMessage");
                        nt.setWhen(System.currentTimeMillis());
                        nt.setContentTitle("Material Recovery Bin");
                        nt.setContentText("The bin is already full!");

                        nmc.notify(1, nt.build());

                    }

                } catch (JSONException e) {
                    e.printStackTrace();
                }


            }

        }
    }
}