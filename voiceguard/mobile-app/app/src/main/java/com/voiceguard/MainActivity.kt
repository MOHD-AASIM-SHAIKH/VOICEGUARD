package com.voiceguard

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import com.voiceguard.ui.screens.VoiceGuardNavHost
import com.voiceguard.ui.theme.VoiceGuardTheme

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            val permissionsToRequest = mutableListOf(
                Manifest.permission.RECORD_AUDIO,
                Manifest.permission.READ_PHONE_STATE
            ).apply {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    add(Manifest.permission.POST_NOTIFICATIONS)
                }
            }

            val permissionLauncher = rememberLauncherForActivityResult(
                contract = ActivityResultContracts.RequestMultiplePermissions()
            ) { perms ->
                if (perms[Manifest.permission.RECORD_AUDIO] == true) {
                    DetectionManager.init(applicationContext)
                }
            }

            LaunchedEffect(Unit) {
                val hasRecordAudio = ContextCompat.checkSelfPermission(
                    this@MainActivity,
                    Manifest.permission.RECORD_AUDIO
                ) == PackageManager.PERMISSION_GRANTED

                if (hasRecordAudio) {
                    DetectionManager.init(applicationContext)
                } else {
                    permissionLauncher.launch(permissionsToRequest.toTypedArray())
                }
            }

            VoiceGuardTheme {
                Surface(
                    modifier = Modifier.fillMaxSize()
                ) {
                    VoiceGuardNavHost()
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
    }
}
