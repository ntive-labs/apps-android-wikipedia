package org.wikipedia.settings

import android.content.Intent
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
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
 *  - `seedActivityData` (Boolean, or the strings `"true"`/`"1"`): seeds the *local* activity data
 *    the Activity tab reads straight off the device rather than off the network — a stored
 *    donation in [Prefs.donationResults] and a handful of reading-history rows. A mock HTTP
 *    backend cannot produce either, because neither is fetched over the network, so this is the
 *    only seam a UI test has for a precondition such as "a stored donation exists". See
 *    [seedLocalActivityData].
 *
 *  - `seedDonationDaysAgo` (Int as a String, default `5`): how long ago the seeded donation
 *    happened. The Activity tab renders it as a relative time ("5 days ago").
 */
object AppConfig {

    const val ARG_API_BASE_URL = "apiBaseUrl"
    const val ARG_DISABLE_CERT_PINNING = "disableCertPinning"
    const val ARG_SEED_ACTIVITY_DATA = "seedActivityData"
    const val ARG_SEED_DONATION_DAYS_AGO = "seedDonationDaysAgo"

    private const val DEFAULT_SEED_DONATION_DAYS_AGO = 5

    /**
     * Articles the seeded reading history is made of. Deliberately the same titles the mock
     * backend serves for the edit-activity modules, so a seeded device looks internally
     * consistent.
     */
    private val SEEDED_READ_ARTICLES = listOf(
        "Maestro (software)" to 900,
        "Android (operating system)" to 720,
        "Wikipedia" to 480
    )

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

        if (extras.containsKey(ARG_SEED_ACTIVITY_DATA) && parseBoolean(extras.get(ARG_SEED_ACTIVITY_DATA))) {
            seedLocalActivityData(parseInt(extras.get(ARG_SEED_DONATION_DAYS_AGO), DEFAULT_SEED_DONATION_DAYS_AGO))
        }
    }

    /**
     * Writes a deterministic stored donation and reading history for the current (mock) wiki.
     *
     * Both are assignments rather than appends, so re-launching with the argument set leaves the
     * device in exactly the same state. Runs synchronously: the Activity tab's view model reads
     * these rows as soon as the tab is first shown, and a background seed would race it.
     */
    private fun seedLocalActivityData(donationDaysAgo: Int) {
        Prefs.donationResults = listOf(
            DonationResult(
                dateTime = LocalDateTime.now().minusDays(donationDaysAgo.toLong()).toString(),
                fromWeb = true,
                amount = 10f,
                currency = "USD",
                recurring = false
            )
        )

        val wikiSite = WikipediaApp.instance.wikiSite
        val now = System.currentTimeMillis()

        runBlocking {
            withContext(Dispatchers.IO) {
                val historyDao = AppDatabase.instance.historyEntryDao()
                val pageImagesDao = AppDatabase.instance.pageImagesDao()
                historyDao.deleteAll()
                SEEDED_READ_ARTICLES.forEachIndexed { index, (title, timeSpentSec) ->
                    val entry = HistoryEntry(
                        title = PageTitle(title, wikiSite),
                        source = HistoryEntry.SOURCE_SEARCH,
                        timestamp = Date(now - TimeUnit.DAYS.toMillis(index.toLong()) - TimeUnit.HOURS.toMillis(1))
                    )
                    historyDao.insertEntry(entry)
                    pageImagesDao.upsertForTimeSpent(entry, timeSpentSec)
                }
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

    private fun parseInt(value: Any?, defaultValue: Int): Int {
        return when (value) {
            is Int -> value
            is String -> value.toIntOrNull() ?: defaultValue
            else -> defaultValue
        }
    }
}
