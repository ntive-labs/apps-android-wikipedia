package org.wikipedia.page.disambiguation

import android.net.Uri
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.CoroutineExceptionHandler
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.launch
import org.wikipedia.dataclient.ServiceFactory
import org.wikipedia.dataclient.WikiSite
import org.wikipedia.page.PageTitle
import org.wikipedia.util.Resource

class DisambiguationViewModel(savedStateHandle: SavedStateHandle) : ViewModel() {

    val wikiSite = savedStateHandle.get<WikiSite>(DisambiguationActivity.EXTRA_WIKI)!!
    private val urls = savedStateHandle.get<ArrayList<String>>(DisambiguationActivity.EXTRA_URLS).orEmpty()

    val similarPagesData = MutableLiveData<Resource<List<PageTitle>>>()

    init {
        loadPages()
    }

    fun loadPages() {
        similarPagesData.postValue(Resource.Loading())
        viewModelScope.launch(CoroutineExceptionHandler { _, throwable ->
            similarPagesData.postValue(Resource.Error(throwable))
        }) {
            // Convert each candidate URL into a PageTitle, deriving the wiki from the URL's
            // authority when possible so cross-wiki links still resolve correctly.
            val titles = urls.mapNotNull { url ->
                runCatching {
                    val uri = Uri.parse(url)
                    val titleWiki = if (!uri.authority.isNullOrEmpty()) WikiSite(uri) else wikiSite
                    PageTitle.titleForUri(uri, titleWiki)
                }.getOrNull()
            }

            // Fetch a summary per candidate concurrently. Drop any candidate whose summary
            // fetch fails (e.g. redirects or missing pages) rather than failing the whole screen.
            val results = titles.map { title ->
                async {
                    runCatching {
                        ServiceFactory.getRest(title.wikiSite)
                            .getPageSummary(title.prefixedText)
                            .getPageTitle(title.wikiSite)
                    }.getOrNull()
                }
            }.awaitAll().filterNotNull()

            if (results.isEmpty()) {
                similarPagesData.postValue(Resource.Error(EmptySimilarPagesException()))
            } else {
                similarPagesData.postValue(Resource.Success(results))
            }
        }
    }

    class EmptySimilarPagesException : RuntimeException()
}
