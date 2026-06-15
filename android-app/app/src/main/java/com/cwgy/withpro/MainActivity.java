package com.cwgy.withpro;

import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    private WebView myWebView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Create WebView dynamically
        myWebView = new WebView(this);
        myWebView.setBackgroundColor(Color.parseColor("#0b0f19")); // dark premium background matching website
        setContentView(myWebView);

        // Configure WebSettings
        WebSettings webSettings = myWebView.getSettings();
        webSettings.setJavaScriptEnabled(true); // Enable JavaScript
        webSettings.setDomStorageEnabled(true); // Enable DOM Storage (essential for modern web apps)
        webSettings.setDatabaseEnabled(true);
        webSettings.setLoadWithOverviewMode(true);
        webSettings.setUseWideViewPort(true);
        webSettings.setSupportZoom(false);
        webSettings.setBuiltInZoomControls(false);
        
        // Optimize WebView performance
        webSettings.setCacheMode(WebSettings.LOAD_DEFAULT);
        
        // Set WebViewClient to handle page navigation in app instead of browser
        myWebView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                // Return false to let the WebView load the URL
                // If the URL is external (not withpro.life), you could launch a browser,
                // but for simplicity and web app wrapper, we let WebView load everything.
                return false;
            }
        });

        // Set WebChromeClient for standard browser events
        myWebView.setWebChromeClient(new WebChromeClient());

        // Load withPRO URL
        myWebView.loadUrl("https://withpro.life");
    }

    @Override
    public void onBackPressed() {
        if (myWebView.canGoBack()) {
            myWebView.goBack(); // Navigate backward inside the webview history
        } else {
            super.onBackPressed(); // Exit the app
        }
    }
}
