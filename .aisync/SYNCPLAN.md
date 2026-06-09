# Sync Plan: Android → iOS

Tracking document for syncing features from this app to the sibling iOS app (`../wikipedia-ios`).
See `APP-SYNC.md` for the overall process.

Commit range: `af457ff7ae` (Hybrid search feature branch, 2026-02-20) through HEAD, oldest first.
For each commit: analyze the change, determine whether the iOS app needs a corresponding change,
then plan and execute it. Check off each commit once it has been dispositioned (synced to iOS or
marked as not applicable).

**Size** = files changed, lines added/removed.

## Commit checklist

| Done | Commit | Date | Author | Size | Summary |
|------|--------|------|--------|------|---------|
| [ ] | `af457ff7ae` | 2026-02-20 | Dmitry Brant | 55f, +2413/−292 | Hybrid search (feature branch) (#6221) |
| [ ] | `eca7eac6e6` | 2026-02-20 | Cooltey Feng | 3f, +39/−15 | Fix: handle dismiss/undo card behavior correctly for WikiGames Card (#6322) |
| [ ] | `ab00f5a8dd` | 2026-02-20 | William Rai | 1f, +3/−1 | Fixes an issue where the Explore feed card visibility didn’t update when toggling languages from the horizontal list in ConfigureActivity (#6338) |
| [ ] | `6c6ce5193c` | 2026-02-23 | translatewiki.net | 25f, +50/−43 | Localisation updates from https://translatewiki.net. (#6339) |
| [ ] | `517351d4cd` | 2026-02-24 | Dmitry Brant | 14f, +289/−46 | Hybrid search: instrumentation. (#6337) |
| [ ] | `e17bbd4e49` | 2026-02-24 | Cooltey Feng | 1f, +10/−1 | Fix: Handle insufficient events for WikiGames and avoid getting stuck in the error page (#6342) |
| [ ] | `cab384d412` | 2026-02-24 | William Rai | 1f, +1/−1 | Bump versionCode. (#6343) |
| [ ] | `7bcbde2866` | 2026-02-25 | William Rai | 1f, +7/−0 | Update testTranslateWikiQQ to fail test if qq contains extra strings (#6344) |
| [ ] | `76534641a9` | 2026-02-25 | dependabot[bot] | 1f, +1/−1 | Bump coilCompose from 3.3.0 to 3.4.0 (#6345) |
| [ ] | `3f5acb1ee9` | 2026-02-26 | translatewiki.net | 6f, +108/−2 | Localisation updates from https://translatewiki.net. (#6349) |
| [ ] | `9512546822` | 2026-02-26 | Cooltey Feng | 1f, +24/−5 | Fix: show the bottom bar even if no results in title-only screen in Semantic search (#6347) |
| [ ] | `4778ade23b` | 2026-02-26 | Cooltey Feng | 3f, +10/−1 | Show up keyboard when showing no results in the title-only screen for Semantic search (#6350) |
| [ ] | `de2684bce4` | 2026-03-02 | translatewiki.net | 6f, +159/−24 | Localisation updates from https://translatewiki.net. (#6354) |
| [ ] | `b7745030f3` | 2026-03-02 | Cooltey Feng | 1f, +1/−1 | Hybrid Search: update learn_button to learn_more (#6352) |
| [ ] | `00dbe762e6` | 2026-03-02 | dependabot[bot] | 1f, +1/−1 | Bump androidx.compose:compose-bom from 2026.02.00 to 2026.02.01 (#6356) |
| [ ] | `fe1486bbed` | 2026-03-03 | Dmitry Brant | 1f, +4/−1 | Fix subtle Game bug when saving progress on last question. (#6360) |
| [ ] | `4824d3a9f7` | 2026-03-03 | Dmitry Brant | 1f, +8/−12 | Adjust Game algorithm to account for days with insufficient events. (#6358) |
| [ ] | `0e5261db2e` | 2026-03-03 | William Rai | 1f, +1/−1 | Bump versionCode. (#6357) |
| [ ] | `837d6a0650` | 2026-03-03 | dependabot[bot] | 1f, +1/−1 | Bump com.android.application from 9.0.1 to 9.1.0 (#6361) |
| [ ] | `13503d1fa2` | 2026-03-03 | dependabot[bot] | 1f, +1/−1 | Bump com.github.skydoves:balloon from 1.7.3 to 1.7.4 (#6362) |
| [ ] | `2e336358d3` | 2026-03-03 | Dmitry Brant | 1f, +1/−1 | Update image dimming coefficient to match mobile web. (#6363) |
| [ ] | `148284e898` | 2026-03-04 | Dmitry Brant | 6f, +26/−27 | Instrumentation: introduce default actionSource parameter. (#6366) |
| [ ] | `29651df144` | 2026-03-04 | dependabot[bot] | 3f, +2/−2 | Bump gradle-wrapper from 9.3.1 to 9.4.0 (#6365) |
| [ ] | `1bb599ca9f` | 2026-03-05 | translatewiki.net | 9f, +236/−15 | Localisation updates from https://translatewiki.net. (#6368) |
| [ ] | `57b418df7d` | 2026-03-06 | Dmitry Brant | 18f, +39/−20 | Upgrade ktlint to 1.8.0. (#6371) |
| [ ] | `26e53d77c0` | 2026-03-06 | dependabot[bot] | 3f, +3/−3 | Bump actions/upload-artifact from 6 to 7 (#6355) |
| [ ] | `5f53119c03` | 2026-03-09 | translatewiki.net | 6f, +31/−8 | Localisation updates from https://translatewiki.net. (#6375) |
| [ ] | `2d908c3384` | 2026-03-09 | Dmitry Brant | 15f, +152/−32 | Instrumentation: underpinnings for sending events to logging intake. (#6370) |
| [ ] | `6240fa0d02` | 2026-03-09 | Dmitry Brant | 6f, +49/−28 | Semantic search: update API, and enable for FR. (#6373) |
| [ ] | `6d0b3e0c4e` | 2026-03-09 | Dmitry Brant | 1f, +10/−10 | Hybrid search: French strings. (#6376) |
| [ ] | `80c5898f4e` | 2026-03-09 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6378) |
| [ ] | `763158c976` | 2026-03-11 | Dmitry Brant | 1f, +8/−1 | Don't log HTTP errors for 320px thumbnail requests. (#6383) |
| [ ] | `e95b52efc6` | 2026-03-11 | Cooltey Feng | 2f, +15/−3 | HybridSearch: French sample queries update (#6382) |
| [ ] | `6c43d3fe3c` | 2026-03-11 | Dmitry Brant | 2f, +12/−4 | Apply User-agent header to MediaPlayer instances. (#6386) |
| [ ] | `8b7b08008f` | 2026-03-11 | Dmitry Brant | 2f, +2/−2 | When matching system Dark theme, default to Dark theme instead of Black. (#6384) |
| [ ] | `bf9aa2a5f7` | 2026-03-11 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6385) |
| [ ] | `232b9d4af5` | 2026-03-12 | dependabot[bot] | 1f, +1/−1 | Bump androidx.activity:activity-compose from 1.12.4 to 1.13.0 (#6390) |
| [ ] | `d535d2d56b` | 2026-03-12 | translatewiki.net | 7f, +75/−16 | Localisation updates from https://translatewiki.net. (#6388) |
| [ ] | `518603c85c` | 2026-03-12 | dependabot[bot] | 1f, +1/−1 | Bump androidx.paging:paging-runtime-ktx from 3.4.1 to 3.4.2 (#6389) |
| [ ] | `64c8c19892` | 2026-03-12 | Dmitry Brant | 6f, +4/−42 | No longer explicitly set user preferences for Push notifications. (#6394) |
| [ ] | `1000bc2690` | 2026-03-12 | dependabot[bot] | 1f, +1/−1 | Bump androidx.paging:paging-compose from 3.4.1 to 3.4.2 (#6393) |
| [ ] | `19f2e7f198` | 2026-03-13 | dependabot[bot] | 1f, +1/−1 | Bump androidx.core:core-ktx from 1.17.0 to 1.18.0 (#6392) |
| [ ] | `15b6c60124` | 2026-03-13 | dependabot[bot] | 1f, +1/−1 | Bump com.github.skydoves:balloon from 1.7.4 to 1.7.5 (#6380) |
| [ ] | `3270449349` | 2026-03-13 | dependabot[bot] | 1f, +1/−1 | Bump androidx.compose:compose-bom from 2026.02.01 to 2026.03.00 (#6391) |
| [ ] | `97ff25cb3d` | 2026-03-16 | translatewiki.net | 3f, +13/−7 | Localisation updates from https://translatewiki.net. (#6395) |
| [ ] | `1765bf32f9` | 2026-03-16 | VeryFat123 | 6f, +7/−16 | No longer use notwikis parameter in notifications API calls. (#6381) |
| [ ] | `a28cfec3f5` | 2026-03-17 | dependabot[bot] | 1f, +1/−1 | Bump ncipollo/release-action from 1.20.0 to 1.21.0 (#6397) |
| [ ] | `fdb9d5722b` | 2026-03-17 | dependabot[bot] | 1f, +1/−1 | Bump kotlinStdlibJdk8 from 2.3.10 to 2.3.20 (#6399) |
| [ ] | `c70a46498a` | 2026-03-17 | William Rai | 55f, +2409/−710 | [Feature Branch] WikiGames Update (#6325) |
| [ ] | `fc23ea01ae` | 2026-03-17 | Dmitry Brant | 2f, +38/−33 | Fix potential crash from re-adding events to queue. (#6403) |
| [ ] | `ea4fc42598` | 2026-03-17 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6404) |
| [ ] | `ffd1c5d115` | 2026-03-17 | Cooltey Feng | 3f, +1/−9 | WikiGames: remove "Learn more" CTA from the snackbar after close (#6402) |
| [ ] | `ca1be9f0af` | 2026-03-17 | William Rai | 5f, +24/−6 | Wikigames design review fixes (#6400) |
| [ ] | `53dfbc934d` | 2026-03-18 | Cooltey Feng | 1f, +14/−12 | WikiGames: do not show image placeholder when the URL is empty (#6406) |
| [ ] | `ed8a5dde85` | 2026-03-18 | Dmitry Brant | 3f, +4/−77 | Semantic search: enable for EN and PT, and rip out for EL. (#6408) |
| [ ] | `f28c0fe37d` | 2026-03-18 | Dmitry Brant | 15f, +5/−246 | Rip out Year-in-Review reading list a/b test. (#6405) |
| [ ] | `b52ce5b270` | 2026-03-18 | Dmitry Brant | 1f, +1/−1 | Fix rate-limiting issue with Random articles in the Feed. (#6410) |
| [ ] | `a91e456007` | 2026-03-18 | Dmitry Brant | 16f, +240/−93 | Instrumentation for authentication workflows. (#6369) |
| [ ] | `9ddfb7f727` | 2026-03-18 | Dmitry Brant | 1f, +3/−10 | Semantic search: fix/simplify progress bar logic. (#6409) |
| [ ] | `63ae0be906` | 2026-03-18 | William Rai | 1f, +1/−1 | - removes the extra padding between the Login button (#6413) |
| [ ] | `73b3b6408a` | 2026-03-19 | translatewiki.net | 52f, +228/−283 | Localisation updates from https://translatewiki.net. (#6415) |
| [ ] | `5be171920e` | 2026-03-19 | Dmitry Brant | 3f, +26/−26 | Semantic search: no longer stuff result lists into actionContext. (#6419) |
| [ ] | `c8c32f212a` | 2026-03-19 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6423) |
| [ ] | `cc4b73a619` | 2026-03-20 | dependabot[bot] | 2f, +2/−2 | Bump gradle-wrapper from 9.4.0 to 9.4.1 (#6418) |
| [ ] | `7a446fbc0e` | 2026-03-20 | Dmitry Brant | 3f, +26/−7 | Semantic search: Portuguese translation update. (#6425) |
| [ ] | `df869fb02e` | 2026-03-20 | Dmitry Brant | 2f, +2/−2 | Event logging: display Toast upon errors in Alpha, not just Dev. (#6426) |
| [ ] | `5eeffeb144` | 2026-03-20 | Dmitry Brant | 3f, +22/−8 | TestKitchen: allow Instrument to set its own MediaWiki dbname. (#6424) |
| [ ] | `8b8b7c2f87` | 2026-03-20 | Dmitry Brant | 7f, +131/−40 | Hybrid search: reintroduce Greek. (#6427) |
| [ ] | `7566c64410` | 2026-03-20 | Dmitry Brant | 1f, +1/−1 | Bump versionCode. (#6429) |
| [ ] | `6e8661bb6a` | 2026-03-20 | William Rai | 1f, +0/−2 | - espresso fixes (#6417) |
| [ ] | `0935bf2406` | 2026-03-23 | translatewiki.net | 10f, +1912/−51 | Localisation updates from https://translatewiki.net. (#6431) |
| [ ] | `051cb9e54c` | 2026-03-23 | Cooltey Feng | 1f, +25/−23 | Fix: possible crash when refresh the WikiGames cards on the Explore Feed (#6430) |
| [ ] | `64d7e74608` | 2026-03-23 | Dmitry Brant | 1f, +14/−3 | Add convenience to BottomSheetDialog to start in expanded state. (#6433) |
| [ ] | `757b433505` | 2026-03-24 | Dmitry Brant | 2f, +1/−2 | Update ktlint rules to add unused-imports rule. (#6437) |
| [ ] | `b50237e6a0` | 2026-03-24 | Dmitry Brant | 1f, +1/−0 | Fix missing callback for HCaptcha instrumentation. (#6438) |
| [ ] | `7c8259f06a` | 2026-03-24 | Dmitry Brant | 1f, +2/−4 | Semantic search instrumentation: send search-id for thumbs up/down. (#6441) |
| [ ] | `ce3b24a1e3` | 2026-03-24 | William Rai | 9f, +61/−15 | Instrumentation for games hub (#6434) |
| [ ] | `f4a1922bcc` | 2026-03-25 | dependabot[bot] | 1f, +1/−1 | Bump androidx.work:work-runtime-ktx from 2.11.1 to 2.11.2 (#6445) |
| [ ] | `8075f8ca3b` | 2026-03-25 | Dmitry Brant | 8f, +119/−95 | Hybrid search: expanded instrumentation. (#6448) |
| [ ] | `bb95b4dea8` | 2026-03-26 | translatewiki.net | 8f, +39/−8 | Localisation updates from https://translatewiki.net. (#6450) |
| [ ] | `cb5af17ea7` | 2026-03-26 | Dmitry Brant | 1f, +1/−1 | Hybrid search: Update verbiage string. (#6451) |
| [ ] | `2d44e869cb` | 2026-03-26 | Dmitry Brant | 1f, +1/−1 | Bump versionCode. (#6454) |
| [ ] | `2fa7fd5f52` | 2026-03-26 | dependabot[bot] | 1f, +1/−1 | Bump androidx.compose:compose-bom from 2026.03.00 to 2026.03.01 (#6452) |
| [ ] | `0f8a7f279f` | 2026-03-26 | William Rai | 2f, +132/−0 | - adds reading challenge widgets (#6455) |
| [ ] | `3c297e3a52` | 2026-03-27 | dependabot[bot] | 1f, +1/−1 | Bump androidx.browser:browser from 1.9.0 to 1.10.0 (#6453) |
| [ ] | `d2a601641b` | 2026-03-27 | dependabot[bot] | 1f, +1/−1 | Bump org.maplibre.gl:android-sdk from 12.2.2 to 12.3.0 (#6189) |
| [ ] | `b2d724fbd1` | 2026-03-27 | Dmitry Brant | 1f, +1/−0 | Don't restart SearchActivity on configuration changes. (#6457) |
| [ ] | `0d33204efd` | 2026-03-30 | translatewiki.net | 29f, +927/−109 | Localisation updates from https://translatewiki.net. (#6462) |
| [ ] | `0614bedaba` | 2026-03-30 | William Rai | 1f, +1/−1 | Bump versionCode. (#6464) |
| [ ] | `c4c6ed86a6` | 2026-03-31 | dependabot[bot] | 1f, +1/−1 | Bump gradle/actions from 5 to 6 (#6463) |
| [ ] | `3db8ee25d7` | 2026-03-31 | Dmitry Brant | 1f, +3/−0 | Add minimal security policy file. (#6466) |
| [ ] | `4180257433` | 2026-03-31 | Dmitry Brant | 1f, +3/−3 | Instrumentation: send create_source with success event. (#6465) |
| [ ] | `36f8e06d60` | 2026-03-31 | Dmitry Brant | 4f, +58/−2 | Allow edge-to-edge for MainActivity, enabling full-bleed compositions. (#6444) |
| [ ] | `9b934fcafd` | 2026-03-31 | Dmitry Brant | 1f, +3/−3 | Properly limit cross-domain sharing of CentralAuth cookies. (#6469) |
| [ ] | `45e09e3135` | 2026-04-01 | Dmitry Brant | 3f, +19/−5 | Verify URLs from VIEW intent before opening. (#6471) |
| [ ] | `6c4c79006f` | 2026-04-01 | Dmitry Brant | 2f, +6/−2 | Limit supported hosts for deeplink scheme. (#6472) |
| [ ] | `d094f168bf` | 2026-04-01 | Dmitry Brant | 3f, +41/−28 | More complete fix of black status bar behind all ActionModes. (#6473) |
| [ ] | `6e625872da` | 2026-04-01 | Dmitry Brant | 1f, +1/−7 | No longer set CORS header on responses passed to WebView. (#6470) |
| [ ] | `b095dea213` | 2026-04-01 | William Rai | 2f, +3/−42 | - override status guard color when action mode is turned on (#6474) |
| [ ] | `4c722eb9b0` | 2026-04-01 | dependabot[bot] | 1f, +1/−1 | Bump org.maplibre.gl:android-sdk from 13.0.1 to 13.0.2 (#6467) |
| [ ] | `41c103e677` | 2026-04-02 | translatewiki.net | 15f, +1181/−42 | Localisation updates from https://translatewiki.net. (#6476) |
| [ ] | `8d884515c2` | 2026-04-03 | Dmitry Brant | 1f, +13/−12 | Improve handling of insets in updated MainActivity. (#6480) |
| [ ] | `b0d9319859` | 2026-04-06 | translatewiki.net | 12f, +466/−12 | Localisation updates from https://translatewiki.net. (#6482) |
| [ ] | `f357109cfa` | 2026-04-06 | William Rai | 1f, +1/−1 | Bump versionCode. (#6483) |
| [ ] | `3e69b4ab40` | 2026-04-08 | Dmitry Brant | 1f, +11/−6 | Fix suggestions to add descriptions when description is empty. (#6487) |
| [ ] | `04482b47eb` | 2026-04-09 | Dmitry Brant | 8f, +1198/−1165 | Periodic update of languages and static data. (#6489) |
| [ ] | `cc34d95920` | 2026-04-09 | translatewiki.net | 11f, +192/−52 | Localisation updates from https://translatewiki.net. (#6490) |
| [ ] | `3368259670` | 2026-04-09 | Dmitry Brant | 1f, +1/−1 | Add "abstract" to list of non-language domains. (#6492) |
| [ ] | `027a1c2d1e` | 2026-04-09 | William Rai | 2f, +2/−2 | Games hub use correct action name (#6486) |
| [ ] | `b07d551b23` | 2026-04-09 | William Rai | 1f, +1/−1 | Bump versionCode. (#6493) |
| [ ] | `2459a1c047` | 2026-04-13 | translatewiki.net | 11f, +423/−38 | Localisation updates from https://translatewiki.net. (#6497) |
| [ ] | `f60a7ee4fd` | 2026-04-13 | William Rai | 1f, +68/−30 | - fixes an issue on the Game Hub preview screen where larger display and font sizes caused the button text to disappear (#6496) |
| [ ] | `2c70e69089` | 2026-04-14 | Dmitry Brant | 1f, +22/−1 | Compose HtmlText: introduce default LinkInteractionListener. (#6491) |
| [ ] | `b74f202c37` | 2026-04-14 | William Rai | 1f, +1/−1 | Bump versionCode. (#6500) |
| [ ] | `053decca72` | 2026-04-14 | dependabot[bot] | 1f, +1/−1 | Bump com.android.application from 9.1.0 to 9.1.1 (#6498) |
| [ ] | `5875c905da` | 2026-04-14 | dependabot[bot] | 1f, +1/−1 | Bump org.jetbrains.kotlinx:kotlinx-serialization-json (#6494) |
| [ ] | `ef040114cd` | 2026-04-16 | translatewiki.net | 12f, +357/−30 | Localisation updates from https://translatewiki.net. (#6505) |
| [ ] | `6cb6efd4d2` | 2026-04-16 | Cooltey Feng | 1f, +1/−1 | Fix: update successColor in Sepia theme to `Green700` (#6506) |
| [ ] | `fb8aca0ae8` | 2026-04-17 | dependabot[bot] | 1f, +1/−1 | Bump com.github.skydoves:balloon from 1.7.5 to 1.7.6 (#6507) |
| [ ] | `c1d6c3ac55` | 2026-04-20 | translatewiki.net | 12f, +68/−10 | Localisation updates from https://translatewiki.net. (#6510) |
| [ ] | `90f57515c6` | 2026-04-20 | dependabot[bot] | 2f, +29/−38 | Bump com.google.android.gms:play-services-wallet from 19.5.0 to 20.0.0 (#6495) |
| [ ] | `98c096bae4` | 2026-04-20 | dependabot[bot] | 1f, +3/−3 | Bump addressable from 2.8.7 to 2.9.0 (#6511) |
| [ ] | `b207fe15c4` | 2026-04-20 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6513) |
| [ ] | `a742986b9a` | 2026-04-21 | dependabot[bot] | 1f, +1/−1 | Bump org.jsoup:jsoup from 1.22.1 to 1.22.2 (#6512) |
| [ ] | `e190b1525e` | 2026-04-21 | Dmitry Brant | 2f, +12/−1 | API model underpinnings for Did You Know. (#6514) |
| [ ] | `06c7f1c5a2` | 2026-04-21 | Dmitry Brant | 5f, +12/−7 | Introduce WikiSite convenience for composable Previews. (#6515) |
| [ ] | `35e34ec577` | 2026-04-23 | translatewiki.net | 11f, +410/−14 | Localisation updates from https://translatewiki.net. (#6523) |
| [ ] | `ff44428c1f` | 2026-04-23 | dependabot[bot] | 1f, +1/−1 | Bump androidx.navigation:navigation-compose from 2.9.7 to 2.9.8 (#6520) |
| [ ] | `438cc0642f` | 2026-04-24 | Dmitry Brant | 3f, +5/−11 | TestKitchen: handle case of streamConfigs being empty, not null. (#6528) |
| [ ] | `e8a40079f3` | 2026-04-24 | William Rai | 2f, +2/−0 | - string update (#6529) |
| [ ] | `af927a671a` | 2026-04-24 | dependabot[bot] | 1f, +2/−2 | Bump the kotlin-ksp group with 2 updates (#6524) |
| [ ] | `99a4268831` | 2026-04-24 | dependabot[bot] | 1f, +1/−1 | Bump com.android.application from 9.1.1 to 9.2.0 (#6517) |
| [ ] | `6d6f67321a` | 2026-04-24 | dependabot[bot] | 3f, +11/−21 | Bump androidx.compose:compose-bom from 2026.03.01 to 2026.04.01 (#6521) |
| [ ] | `b1dab4139e` | 2026-04-27 | translatewiki.net | 18f, +389/−10 | Localisation updates from https://translatewiki.net. (#6532) |
| [ ] | `e5652ed35b` | 2026-04-27 | Dmitry Brant | 1f, +10/−0 | TestKitchen: Flush events periodically, not just when closing activity. (#6535) |
| [ ] | `52102be0fa` | 2026-04-27 | William Rai | 64f, +4060/−24 | [Feature branch] Reading challenge widget (#6367) |
| [ ] | `121aead5ce` | 2026-04-27 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6536) |
| [ ] | `fab8dc862a` | 2026-04-28 | dependabot[bot] | 1f, +1/−1 | Bump androidx.compose.ui:ui-graphics from 1.10.5 to 1.11.0 (#6539) |
| [ ] | `b378a889fd` | 2026-04-28 | William Rai | 3f, +109/−78 | [Reading Challenge Widget] Widget Size Optimization Using percentage layout (#6541) |
| [ ] | `356653f6da` | 2026-04-28 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6543) |
| [ ] | `a26078813e` | 2026-04-30 | translatewiki.net | 10f, +190/−6 | Localisation updates from https://translatewiki.net. (#6548) |
| [ ] | `36c5590720` | 2026-04-30 | William Rai | 7f, +279/−107 | [Reading Challenge Widget] Fixes missing behavior logic (#6544) |
| [ ] | `3b438fd1da` | 2026-04-30 | Cooltey Feng | 1f, +38/−29 | [ReadingChallenge] Fix: make content scrollable if the text size is too large (#6547) |
| [ ] | `09ec2aafff` | 2026-04-30 | Cooltey Feng | 6f, +50/−18 | [ReadingChallenge] Fix: tap on join challenge should always show the prompt (#6545) |
| [ ] | `4c7555162d` | 2026-04-30 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6550) |
| [ ] | `54f9b3b3e9` | 2026-05-01 | Dmitry Brant | 158f, +7048/−0 | Add static Topics translations. (#6549) |
| [ ] | `f37f2a796b` | 2026-05-01 | Dmitry Brant | 1f, +210/−0 | Introduce Topics list for general use. (#6552) |
| [ ] | `4db3feffe3` | 2026-05-01 | Dmitry Brant | 1f, +81/−0 | Introduce composable for fading-in AsyncImage. (#6551) |
| [ ] | `7f54a97dd8` | 2026-05-01 | William Rai | 2f, +30/−25 | [Reading Challenge Widget] Fix mascot disappearing (#6554) |
| [ ] | `45b0254058` | 2026-05-04 | translatewiki.net | 5f, +213/−12 | Localisation updates from https://translatewiki.net. (#6555) |
| [ ] | `eb5445a922` | 2026-05-04 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6556) |
| [ ] | `d5ee543659` | 2026-05-05 | dependabot[bot] | 1f, +1/−1 | Bump com.android.application from 9.2.0 to 9.2.1 (#6558) |
| [ ] | `6e43ec8bd6` | 2026-05-06 | dependabot[bot] | 4f, +14/−23 | Bump gradle-wrapper from 9.4.1 to 9.5.0 (#6540) |
| [ ] | `cfd2673de8` | 2026-05-06 | dependabot[bot] | 1f, +1/−1 | Bump androidx.paging:paging-runtime-ktx from 3.4.2 to 3.5.0 (#6560) |
| [ ] | `d296b7efbb` | 2026-05-06 | dependabot[bot] | 1f, +1/−1 | Bump androidx.paging:paging-compose from 3.4.2 to 3.5.0 (#6562) |
| [ ] | `da70859dd6` | 2026-05-06 | dependabot[bot] | 1f, +1/−1 | Bump androidx.compose:compose-bom from 2026.04.01 to 2026.05.00 (#6561) |
| [ ] | `81c63185ad` | 2026-05-06 | dependabot[bot] | 1f, +1/−1 | Bump androidx.compose.ui:ui-graphics from 1.11.0 to 1.11.1 (#6563) |
| [ ] | `198531f0c5` | 2026-05-06 | William Rai | 1f, +1/−0 | - adds instrumentation for ChallengeRemoved state (#6567) |
| [ ] | `05392ea39b` | 2026-05-06 | William Rai | 1f, +1/−0 | Remove Notification View from Explore Feed when user logs out (#6566) |
| [ ] | `f730d59705` | 2026-05-06 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6569) |
| [ ] | `07dd3fd517` | 2026-05-07 | translatewiki.net | 2f, +76/−7 | Localisation updates from https://translatewiki.net. (#6572) |
| [ ] | `4a3e1357d7` | 2026-05-07 | Cooltey Feng | 2f, +6/−0 | Fix: use legacy zh-classical as the subdomain instead of lzh (#6571) |
| [ ] | `2bb026367d` | 2026-05-07 | Dmitry Brant | 4f, +11/−11 | Design tweaks to Dot pager indicators. (#6570) |
| [ ] | `2f95dddb34` | 2026-05-08 | Uwe Martin | 1f, +3/−1 | Using higher contrast text background color when in black or dark mode. (#6531) |
| [ ] | `99aa556e88` | 2026-05-08 | Cooltey Feng | 1f, +5/−35 | Remove migration code and fix possible error in the WikiGames (#6574) |
| [ ] | `c46e647f55` | 2026-05-08 | Dmitry Brant | 7f, +30/−18 | Make ReadingLists correctly use remote Create and Modify time. (#6575) |
| [ ] | `b88c6a672e` | 2026-05-11 | translatewiki.net | 10f, +229/−31 | Localisation updates from https://translatewiki.net. (#6579) |
| [ ] | `996ad8592f` | 2026-05-11 | Dmitry Brant | 1f, +3/−3 | Strip style tags when displaying Wiktionary definitions. (#6580) |
| [ ] | `40876929c5` | 2026-05-12 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6584) |
| [ ] | `684d2bc170` | 2026-05-12 | Stefan Sundin | 3f, +5/−1 | Configure `android:windowSplashScreenBackground` to avoid white flash when the app opens in dark mode. (#6577) |
| [ ] | `7327ad2d0e` | 2026-05-13 | dependabot[bot] | 1f, +1/−1 | Bump gradle-wrapper from 9.5.0 to 9.5.1 (#6585) |
| [ ] | `a3ac44de89` | 2026-05-13 | Dmitry Brant | 2f, +114/−0 | Strings for Home Feed. (#6586) |
| [ ] | `abfb3f82e0` | 2026-05-13 | William Rai | 2f, +16/−6 | Additional strings for the Home feed (#6587) |
| [ ] | `2b65f37182` | 2026-05-13 | Gyrandola | 1f, +1/−1 | Fix: increases search widget medium-size threshold (#6522) |
| [ ] | `29e8261693` | 2026-05-13 | Cooltey Feng | 10f, +90/−37 | Instrumentation for app_open events (#6576) |
| [ ] | `64da8320a4` | 2026-05-13 | Cooltey Feng | 2f, +17/−13 | Add strings for swipe-to-explore prompt in the new explore feed (#6589) |
| [ ] | `f1d1a94f86` | 2026-05-14 | Cooltey Feng | 2f, +2/−2 | Fix: add the correct contentDescription to the close icon in tab items (#6593) |
| [ ] | `365bd9be6f` | 2026-05-14 | William Rai | 2f, +8/−0 | - strings for empty state (#6594) |
| [ ] | `faea574716` | 2026-05-14 | dependabot[bot] | 1f, +1/−1 | Bump com.google.devtools.ksp from 2.3.7 to 2.3.8 in the kotlin-ksp group (#6588) |
| [ ] | `027acdf6b3` | 2026-05-14 | dependabot[bot] | 1f, +1/−1 | Bump com.google.android.material:material from 1.13.0 to 1.14.0 (#6590) |
| [ ] | `98a3120b79` | 2026-05-15 | William Rai | 1f, +1/−1 | - string update (#6600) |
| [ ] | `d9630fab94` | 2026-05-18 | translatewiki.net | 22f, +924/−120 | Localisation updates from https://translatewiki.net. (#6602) |
| [ ] | `836543c9f7` | 2026-05-18 | William Rai | 2f, +10/−0 | [Explore Feed] For you empty state strings (#6603) |
| [ ] | `bf13277f15` | 2026-05-18 | Cooltey Feng | 1f, +30/−8 | Update AGENTS.md (#6564) |
| [ ] | `51ea875719` | 2026-05-19 | Dmitry Brant | 1f, +6/−0 | Add unit test for transforming thumbnail URLs with URL parameters. (#6605) |
| [ ] | `e164df3609` | 2026-05-19 | William Rai | 2f, +18/−0 | - strings for what's driving your feed setting (#6608) |
| [ ] | `19668e0979` | 2026-05-19 | Dmitry Brant | 2f, +2/−9 | Test kitchen: Limit max number of languages in performerData. (#6609) |
| [ ] | `efeefd187c` | 2026-05-20 | dependabot[bot] | 1f, +1/−1 | Bump androidx.compose.ui:ui-graphics from 1.11.1 to 1.11.2 (#6611) |
| [ ] | `89ae7913a7` | 2026-05-20 | dependabot[bot] | 1f, +1/−1 | Bump androidx.compose:compose-bom from 2026.05.00 to 2026.05.01 (#6612) |
| [ ] | `016fff831f` | 2026-05-21 | translatewiki.net | 16f, +513/−30 | Localisation updates from https://translatewiki.net. (#6617) |
| [ ] | `20cc80172d` | 2026-05-21 | Cooltey Feng | 144f, +11011/−560 | [Feature branch] Explore Feed Redesign (#6446) |
| [ ] | `d526598ac6` | 2026-05-21 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6620) |
| [ ] | `50424247f4` | 2026-05-21 | Cooltey Feng | 4f, +8/−3 | Fix: update the homeLanguage during onboarding and undo the changes in updateSelectedLanguageIfNeeded (#6621) |
| [ ] | `8cbc88d004` | 2026-05-21 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6622) |
| [ ] | `4260ebcfce` | 2026-05-22 | Dmitry Brant | 1f, +9/−20 | Show announcements by allowlist, not denylist. (#6624) |
| [ ] | `8268b4a251` | 2026-05-22 | William Rai | 1f, +1/−1 | - string update (#6625) |
| [ ] | `f74f200812` | 2026-05-22 | Cooltey Feng | 1f, +18/−4 | Fix: refresh the Feed content when the language is inconsistent (#6623) |
| [ ] | `29604f7c71` | 2026-05-22 | Dmitry Brant | 3f, +34/−36 | Home feed: Tweak/improve Continue Reading logic. (#6626) |
| [ ] | `d827c1b03c` | 2026-05-26 | translatewiki.net | 84f, +766/−442 | Localisation updates from https://translatewiki.net. (#6633) |
| [ ] | `d11edd58e3` | 2026-05-26 | Cooltey Feng | 1f, +14/−7 | Fix: when the tab icon or notification icon appears, the toolbar moves (#6630) |
| [ ] | `36aab1c3fd` | 2026-05-26 | Dmitry Brant | 2f, +336/−319 | Home feed: properly use RTL or LTR layout based on language. (#6634) |
| [ ] | `e97b3b6af3` | 2026-05-26 | Cooltey Feng | 1f, +1/−0 | Fix: image caption and license should be visible by default (#6635) |
| [ ] | `6d890ec0a3` | 2026-05-26 | Cooltey Feng | 2f, +32/−5 | Fix: use LaunchedEffect to resolve the overflow animation issue on (#6629) |
| [ ] | `7311d3d1c3` | 2026-05-26 | Hakan | 2f, +144/−6 | Fix nested display:none span handling in CustomHtmlParser (#6631) |
| [ ] | `b7ac078dad` | 2026-05-26 | Dmitry Brant | 2f, +8/−4 | Improve display of Blocked messages, and make snackbar selectable. (#6636) |
| [ ] | `ab19004b73` | 2026-05-26 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6638) |
| [ ] | `49381781fa` | 2026-05-27 | dependabot[bot] | 1f, +1/−1 | Bump com.google.devtools.ksp from 2.3.8 to 2.3.9 in the kotlin-ksp group (#6639) |
| [ ] | `026dbd6c8b` | 2026-05-27 | William Rai | 2f, +22/−29 | - multiples recomposition fixes in pageIndicator and FadeAsyncImage (#6637) |
| [ ] | `c40da836be` | 2026-05-27 | Dmitry Brant | 1f, +1/−2 | Home feed: set funnel name when initializing. (#6641) |
| [ ] | `480a19f0aa` | 2026-05-27 | William Rai | 5f, +1463/−1337 | - splits home fragment to dedicated composables. ForYouContentTab.kt, CommunityContentTab.kt, HomeScreen.kt and shared FeedComponents.kt. (#6640) |
| [ ] | `1b52136556` | 2026-05-28 | translatewiki.net | 13f, +353/−48 | Localisation updates from https://translatewiki.net. (#6644) |
| [ ] | `0c4d8a2e33` | 2026-05-28 | Cooltey Feng | 1f, +1/−1 | Bump versionCode. (#6645) |
| [ ] | `e690c486af` | 2026-05-29 | Cooltey Feng | 1f, +1/−1 | Fix: avoid showing duplicated continue reading articles in Home feed. (#6646) |
| [ ] | `fbbc8c6f57` | 2026-06-01 | translatewiki.net | 12f, +725/−26 | Localisation updates from https://translatewiki.net. (#6651) |
| [ ] | `052d4fff08` | 2026-06-01 | William Rai | 2f, +17/−24 | - reloads reactively when language and tab changes (#6628) |
| [ ] | `7d405c6736` | 2026-06-01 | Brooke Vibber | 1f, +4/−3 | Update address for bvibber (#6653) |
| [ ] | `2cbae2b837` | 2026-06-01 | Cooltey Feng | 133f, +77/−6957 | Clean up Explore feed codes (#6649) |
| [ ] | `08116872ab` | 2026-06-01 | Dmitry Brant | 1f, +2/−2 | Fix potential crash when displaying overflow menu in Notifications. (#6652) |
| [ ] | `e422eb7a01` | 2026-06-02 | Dmitry Brant | 14f, +39/−165 | Further cleanup of old Explore feed, and fixes. (#6654) |
| [ ] | `e98c308a68` | 2026-06-02 | Dmitry Brant | 1f, +60/−0 | Randomizer: enable shake-to-shuffle. (#6655) |
| [ ] | `b5145a8c2a` | 2026-06-02 | William Rai | 7f, +265/−115 | [Explore Feed] For you content end of feed (#6642) |
| [ ] | `440b6555bb` | 2026-06-02 | William Rai | 1f, +1/−1 | Bump versionCode. (#6657) |
| [ ] | `c2c5fc3c9a` | 2026-06-04 | translatewiki.net | 9f, +39/−14 | Localisation updates from https://translatewiki.net. (#6661) |
| [ ] | `df875dc049` | 2026-06-04 | Dmitry Brant | 1f, +91/−82 | Possible fix for T395597 (#6659) |
| [ ] | `4f936f143a` | 2026-06-04 | William Rai | 26f, +45/−881 | [Explore feed] Android instrumented test cleanup (#6656) |
| [ ] | `da68484428` | 2026-06-04 | Tyler Heck | 20f, +289/−80 | T427722: Update Launcher Icon and Splash Screen (#6650) |
| [ ] | `09917ef4b2` | 2026-06-04 | William Rai | 6f, +100/−100 | [Explore Feed] reactive hidden card using data store  (#6658) |
| [ ] | `3a901fcf6e` | 2026-06-05 | Dmitry Brant | 12f, +346/−3 | Home Feed: Did You Know (#6662) |
| [ ] | `171fa6650c` | 2026-06-05 | Dmitry Brant | 11f, +71/−191 | Introduce preview conveniences for PageTitle and PageSummary. (#6664) |
| [ ] | `9de3822311` | 2026-06-05 | Dmitry Brant | 10f, +223/−15 | Home Feed: Random article (#6663) |
| [ ] | `ae1c137422` | 2026-06-08 | translatewiki.net | 16f, +126/−19 | Localisation updates from https://translatewiki.net. (#6665) |
| [ ] | `ac1fc58efd` | 2026-06-08 | William Rai | 17f, +528/−17 | [Explore Feed] Places of Interest Module (#6648) |
| [ ] | `dd6b000088` | 2026-06-08 | William Rai | 1f, +1/−1 | Bump versionCode. (#6666) |
| [ ] | `f59bc9aafe` | 2026-06-09 | Kevin Galligan | 1f, +10/−0 | sync plan |
