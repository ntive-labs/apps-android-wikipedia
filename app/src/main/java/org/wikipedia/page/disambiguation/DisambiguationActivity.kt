package org.wikipedia.page.disambiguation

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.view.ViewGroup
import androidx.activity.viewModels
import androidx.core.view.isVisible
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import kotlinx.coroutines.launch
import org.wikipedia.R
import org.wikipedia.activity.BaseActivity
import org.wikipedia.databinding.ActivityDisambiguationBinding
import org.wikipedia.dataclient.WikiSite
import org.wikipedia.extensions.setLayoutDirectionByLang
import org.wikipedia.history.HistoryEntry
import org.wikipedia.page.PageActivity
import org.wikipedia.page.PageTitle
import org.wikipedia.readinglist.database.ReadingList
import org.wikipedia.util.Resource
import org.wikipedia.util.ResourceUtil
import org.wikipedia.views.DrawableItemDecoration
import org.wikipedia.views.PageItemView

// Android counterpart to iOS's DisambiguationPagesViewController: a dedicated, navigable
// "Similar pages" list built from a disambiguation article's candidate links, each rendered
// with title + description + thumbnail. Tapping a candidate opens it in the article reader via
// PageActivity.newIntentForNewTab (the same new-tab navigation every other footer/list screen
// in the app uses), so the reader's singleTask task comes forward for continued reading.
class DisambiguationActivity : BaseActivity() {
    private lateinit var binding: ActivityDisambiguationBinding
    private val viewModel: DisambiguationViewModel by viewModels()
    private val itemCallback = ItemCallback()
    private val disambiguationAdapter = DisambiguationAdapter()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDisambiguationBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setStatusBarColor(ResourceUtil.getThemedColor(this, android.R.attr.windowBackground))
        setSupportActionBar(binding.disambigToolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.setDisplayShowTitleEnabled(false)
        binding.disambigToolbarTitle.setText(R.string.page_similar_titles)

        binding.root.setLayoutDirectionByLang(viewModel.wikiSite.languageCode)
        binding.disambigRecycler.layoutManager = LinearLayoutManager(this)
        binding.disambigRecycler.addItemDecoration(DrawableItemDecoration(this, R.attr.list_divider, drawStart = false, drawEnd = false))
        binding.disambigRecycler.adapter = disambiguationAdapter

        binding.disambigErrorView.retryClickListener = View.OnClickListener { viewModel.loadPages() }
        binding.disambigErrorView.backClickListener = View.OnClickListener { onBackPressedDispatcher.onBackPressed() }

        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    when (state) {
                        is Resource.Loading -> showLoading()
                        is Resource.Success -> showResults(state.data)
                        is Resource.Error -> showError(state.throwable)
                    }
                }
            }
        }
    }

    private fun showLoading() {
        binding.disambigProgressBar.isVisible = true
        binding.disambigErrorView.isVisible = false
        binding.disambigRecycler.isVisible = false
    }

    private fun showResults(titles: List<PageTitle>) {
        binding.disambigProgressBar.isVisible = false
        binding.disambigErrorView.isVisible = false
        binding.disambigRecycler.isVisible = true
        disambiguationAdapter.setItems(titles)
    }

    private fun showError(throwable: Throwable) {
        binding.disambigProgressBar.isVisible = false
        binding.disambigRecycler.isVisible = false
        binding.disambigErrorView.setError(throwable)
        binding.disambigErrorView.isVisible = true
    }

    private fun openPage(title: PageTitle) {
        val entry = HistoryEntry(title, HistoryEntry.SOURCE_DISAMBIG)
        startActivity(PageActivity.newIntentForNewTab(this, entry, title))
    }

    private inner class DisambiguationItemHolder(val view: PageItemView<PageTitle>) : RecyclerView.ViewHolder(view) {
        fun bindItem(title: PageTitle) {
            view.item = title
            view.setTitle(title.displayText)
            view.setDescription(title.description)
            view.setImageUrl(title.thumbUrl)
            view.setImageVisible(!title.thumbUrl.isNullOrEmpty())
        }
    }

    private inner class DisambiguationAdapter : RecyclerView.Adapter<DisambiguationItemHolder>() {
        private val items = mutableListOf<PageTitle>()

        @SuppressLint("NotifyDataSetChanged")
        fun setItems(titles: List<PageTitle>) {
            items.clear()
            items.addAll(titles)
            notifyDataSetChanged()
        }

        override fun getItemCount(): Int {
            return items.size
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): DisambiguationItemHolder {
            val view = PageItemView<PageTitle>(this@DisambiguationActivity)
            view.callback = itemCallback
            return DisambiguationItemHolder(view)
        }

        override fun onBindViewHolder(holder: DisambiguationItemHolder, position: Int) {
            holder.bindItem(items[position])
        }
    }

    private inner class ItemCallback : PageItemView.Callback<PageTitle?> {
        override fun onClick(item: PageTitle?) {
            item?.let { openPage(it) }
        }

        override fun onLongClick(item: PageTitle?): Boolean {
            return false
        }

        override fun onActionClick(item: PageTitle?, view: View) {}

        override fun onListChipClick(readingList: ReadingList) {}
    }

    companion object {
        const val EXTRA_WIKI = "wiki"
        const val EXTRA_URLS = "urls"

        fun newIntent(context: Context, wiki: WikiSite, urls: List<String>): Intent {
            return Intent(context, DisambiguationActivity::class.java)
                .putExtra(EXTRA_WIKI, wiki)
                .putStringArrayListExtra(EXTRA_URLS, ArrayList(urls))
        }
    }
}
