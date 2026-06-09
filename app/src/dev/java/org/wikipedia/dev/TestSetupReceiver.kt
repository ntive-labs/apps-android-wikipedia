package org.wikipedia.dev

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import org.wikipedia.settings.PrefsIoUtil
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

    override fun onReceive(context: Context, intent: Intent) {
        val prefsJson = intent.getStringExtra(EXTRA_PREFS)
        if (prefsJson.isNullOrEmpty()) {
            L.w("TestSetupReceiver: no \"$EXTRA_PREFS\" extra provided")
            return
        }
        var count = 0
        try {
            Json.parseToJsonElement(prefsJson).jsonObject.forEach { (key, element) ->
                val primitive = element.jsonPrimitive
                when {
                    primitive.booleanOrNull != null -> PrefsIoUtil.setBoolean(key, primitive.booleanOrNull!!)
                    primitive.intOrNull != null -> PrefsIoUtil.setInt(key, primitive.intOrNull!!)
                    primitive.longOrNull != null -> PrefsIoUtil.setLong(key, primitive.longOrNull!!)
                    else -> PrefsIoUtil.setString(key, primitive.content)
                }
                count++
            }
        } catch (e: Exception) {
            L.e("TestSetupReceiver: failed to parse prefs JSON: $prefsJson", e)
            resultCode = -1
            return
        }
        L.d("TestSetupReceiver: seeded $count preference(s)")
        resultCode = count
    }

    companion object {
        const val EXTRA_PREFS = "prefs"
    }
}
