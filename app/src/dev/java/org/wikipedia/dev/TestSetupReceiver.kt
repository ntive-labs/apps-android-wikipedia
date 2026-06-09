package org.wikipedia.dev

import android.annotation.SuppressLint
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.preference.PreferenceManager
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import org.wikipedia.util.log.L

/**
 * Dev-flavor-only hook that lets UI test harnesses (e.g. Maestro) seed app state
 * before a test flow launches the app. See .maestro/MOCKING.md for usage.
 *
 * Invoke via adb, then force-stop the app so the seeded preferences are read
 * fresh on the next launch:
 *
 *   adb shell am broadcast \
 *     -n org.wikipedia.dev/org.wikipedia.dev.TestSetupReceiver \
 *     --es prefs "'{\"initialOnboardingEnabled\":false}'"
 *   adb shell am force-stop org.wikipedia.dev
 *
 * The "prefs" extra is a JSON object whose keys are SharedPreferences key strings
 * (the values in res/values/preference_keys.xml, not the resource names) and whose
 * values are written with a matching type (boolean, int, long, or string).
 */
class TestSetupReceiver : BroadcastReceiver() {

    @SuppressLint("ApplySharedPref")
    override fun onReceive(context: Context, intent: Intent) {
        val prefsJson = intent.getStringExtra(EXTRA_PREFS)
        if (prefsJson.isNullOrEmpty()) {
            L.w("TestSetupReceiver: no \"$EXTRA_PREFS\" extra provided")
            return
        }
        var count = 0
        // Write through a single editor and commit() synchronously: the caller
        // force-stops the app right after this broadcast, which would discard
        // pending async apply() writes.
        val editor = PreferenceManager.getDefaultSharedPreferences(context).edit()
        try {
            Json.parseToJsonElement(prefsJson).jsonObject.forEach { (key, element) ->
                val primitive = element.jsonPrimitive
                when {
                    primitive.booleanOrNull != null -> editor.putBoolean(key, primitive.booleanOrNull!!)
                    primitive.intOrNull != null -> editor.putInt(key, primitive.intOrNull!!)
                    primitive.longOrNull != null -> editor.putLong(key, primitive.longOrNull!!)
                    else -> editor.putString(key, primitive.content)
                }
                count++
            }
        } catch (e: Exception) {
            L.e("TestSetupReceiver: failed to parse prefs JSON: $prefsJson", e)
            resultCode = -1
            return
        }
        editor.commit()
        L.d("TestSetupReceiver: seeded $count preference(s)")
        resultCode = count
    }

    companion object {
        const val EXTRA_PREFS = "prefs"
    }
}
