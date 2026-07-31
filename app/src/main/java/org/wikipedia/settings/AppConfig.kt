package org.wikipedia.settings

import android.content.Intent
import org.wikipedia.BuildConfig
import org.wikipedia.WikipediaApp
import org.wikipedia.dataclient.WikiSite

/**
 * Holds launch-time configuration overrides that let a Maestro UI test point the app at a mock
 * backend (e.g. WireMock running on the host) instead of the production Wikipedia servers.
 *
 * Everything here is hard-gated to debug builds ([BuildConfig.DEBUG]) so none of it can ever run
 * in a release build.
 *
 * Launch arguments arrive as extras on the launcher intent (set by Maestro's `launchApp.arguments`)
 * and are applied from [org.wikipedia.main.MainActivity.onCreate] before the first network call:
 *
 *  - `apiBaseUrl` (String): full base URL of the mock server, e.g. `http://10.0.2.2:8080`
 *    (`10.0.2.2` is the host loopback as seen from the Android emulator). When set, the app's
 *    "home" wiki — which drives the MediaWiki action API (`/w/api.php`), the REST v1 API
 *    (`/api/rest_v1/`) and the core REST API (`/w/rest.php/`) — is pointed at this host.
 *
 *  - `disableCertPinning` (Boolean, or the strings `"true"`/`"1"`): the app does not use OkHttp
 *    certificate pinning, so this is informational on Android. Debug builds already permit
 *    cleartext traffic via `src/debug/res/xml/network_security_config.xml`, which is what lets the
 *    plain-HTTP mock traffic through. The parsed value is exposed as [certPinningEnabled] for
 *    parity with iOS and any future use.
 */
object AppConfig {

    const val ARG_API_BASE_URL = "apiBaseUrl"
    const val ARG_DISABLE_CERT_PINNING = "disableCertPinning"

    var apiBaseUrl: String = ""
        private set

    var certPinningEnabled: Boolean = true
        private set

    val hasApiBaseUrlOverride get() = apiBaseUrl.isNotEmpty()

    fun applyLaunchOverrides(intent: Intent?) {
        if (!BuildConfig.DEBUG) {
            return // hard gate — never in release
        }
        val extras = intent?.extras ?: return

        extras.getString(ARG_API_BASE_URL)?.trim()?.takeIf { it.isNotEmpty() }?.let { apiBaseUrl = it }

        if (extras.containsKey(ARG_DISABLE_CERT_PINNING)) {
            certPinningEnabled = !parseBoolean(extras.get(ARG_DISABLE_CERT_PINNING))
        }

        if (hasApiBaseUrlOverride) {
            // Point the default "home" wiki at the mock host and drop the cached wiki site so it is
            // rebuilt from the override on next access, before any core-flow request is made.
            // The full URL (with scheme) is required so WikiSite can parse the authority for its
            // own link-routing checks (supportedAuthority).
            WikiSite.setDefaultBaseUrl(apiBaseUrl)
            WikipediaApp.instance.resetWikiSite()
        }
    }

    // Maestro may deliver the value as a real Boolean extra or as a String, so accept both.
    private fun parseBoolean(value: Any?): Boolean {
        return when (value) {
            is Boolean -> value
            is String -> value.equals("true", ignoreCase = true) || value == "1"
            else -> false
        }
    }
}
