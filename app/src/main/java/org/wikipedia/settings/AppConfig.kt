package org.wikipedia.settings

import android.content.Intent
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import org.wikipedia.BuildConfig
import org.wikipedia.WikipediaApp
import org.wikipedia.database.AppDatabase
import org.wikipedia.dataclient.WikiSite
import org.wikipedia.donate.DonationResult
import org.wikipedia.history.HistoryEntry
import org.wikipedia.page.PageTitle
import java.time.LocalDateTime
import java.util.Date
import java.util.concurrent.TimeUnit

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
 *
 *  - `mockActivityData` (Boolean, or the strings `"true"`/`"1"`): seeds the *locally stored*
 *    activity data that the Activity tab reads but that no API can supply — a donation in
 *    [Prefs.donationResults] and a couple of recently read articles (with time spent) in the
 *    history database. See [seedActivityData].
 */
object AppConfig {

    const val ARG_API_BASE_URL = "apiBaseUrl"
    const val ARG_DISABLE_CERT_PINNING = "disableCertPinning"
    const val ARG_MOCK_ACTIVITY_DATA = "mockActivityData"

    private const val MOCK_DONATION_DAYS_AGO = 3L
    private const val MOCK_DONATION_AMOUNT = 5f
    private const val MOCK_DONATION_CURRENCY = "USD"
    private const val MOCK_TIME_SPENT_SEC = 900
    private val MOCK_READ_ARTICLES = listOf("Maestro (software)", "Android (operating system)")

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

        if (parseBoolean(extras.get(ARG_MOCK_ACTIVITY_DATA))) {
            seedActivityData()
        }
    }

    /**
     * Populates the parts of the Activity tab's data that live on the device rather than behind an
     * API, so a UI test can start from a known, non-empty activity state:
     *
     *  - one [DonationResult] a few days old, which is what makes the Donation History module both
     *    configurable and visible ([org.wikipedia.activitytab.ModuleType.DONATIONS]), and
     *  - a couple of recently read articles with time spent on them, which is what the reading
     *    history module and the reading half of the timeline are built from.
     *
     * Edit activity is not seeded here: it comes from the API, i.e. from the mock server that
     * [ARG_API_BASE_URL] points the app at.
     */
    private fun seedActivityData() {
        Prefs.donationResults = listOf(
            DonationResult(
                dateTime = LocalDateTime.now().minusDays(MOCK_DONATION_DAYS_AGO).toString(),
                fromWeb = false,
                amount = MOCK_DONATION_AMOUNT,
                currency = MOCK_DONATION_CURRENCY,
                recurring = false
            )
        )

        CoroutineScope(Dispatchers.IO).launch {
            val wikiSite = WikipediaApp.instance.wikiSite
            MOCK_READ_ARTICLES.forEachIndexed { index, title ->
                val entry = HistoryEntry(
                    title = PageTitle(title, wikiSite),
                    source = HistoryEntry.SOURCE_SEARCH,
                    timestamp = Date(System.currentTimeMillis() - TimeUnit.HOURS.toMillis(index + 1L))
                )
                AppDatabase.instance.historyEntryDao().insert(listOf(entry))
                AppDatabase.instance.pageImagesDao().upsertForTimeSpent(entry, MOCK_TIME_SPENT_SEC)
            }
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
