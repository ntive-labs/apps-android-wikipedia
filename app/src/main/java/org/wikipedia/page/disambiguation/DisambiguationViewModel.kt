package org.wikipedia.page.disambiguation

import android.net.Uri
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.CoroutineExceptionHandler
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.wikipedia.dataclient.ServiceFactory
import org.wikipedia.dataclient.WikiSite
import org.wikipedia.page.PageTitle
import org.wikipedia.util.Resource

class DisambiguationViewModel(savedStateHandle: SavedStateHandle) : ViewModel() {

    val wikiSite = savedStateHandle.get<WikiSite>(DisambiguationActivity.EXTRA_WIKI)!!
    private val urls = savedStateHandle.get<ArrayList<String>>(DisambiguationActivity.EXTRA_URLS).orEmpty()

    private val _uiState = MutableStateFlow<Resource<List<PageTitle>>>(Resource.Loading())
    val uiState = _uiState.asStateFlow()

    init {
        loadPages()
    }

    fun loadPages() {
        _uiState.value = Resource.Loading()
        viewModelScope.launch(CoroutineExceptionHandler { _, throwable ->
            _uiState.value = Resource.Error(throwable)
        }) {
            // Convert each candidate URL into a PageTitle, deriving its wiki from the URL
            // authority where possible, and falling back to the source article's wiki.
            val titles = urls.mapNotNull { url ->
                runCatching {
                    val uri = Uri.parse(url)
                    val wiki = if (!uri.authority.isNullOrEmpty()) WikiSite(uri) else wikiSite
                    PageTitle.titleForUri(uri, wiki)
                }.getOrNull()
            }

            // Fetch summaries concurrently so we can show title + description + thumbnail rows.
            // A candidate whose summary can't be fetched (e.g. redirect/missing) is dropped
            // rather than failing the whole screen; input order is preserved.
            val results = titles.map { title ->
                async {
                    runCatching {
                        ServiceFactory.getRest(title.wikiSite)
                            .getPageSummary(title.prefixedText)
                            .getPageTitle(title.wikiSite)
                    }.getOrNull()
                }
            }.awaitAll().filterNotNull()

            _uiState.value = if (results.isEmpty()) {
                Resource.Error(RuntimeException("No similar pages found."))
            } else {
                Resource.Success(results)
            }
        }
    }
}
