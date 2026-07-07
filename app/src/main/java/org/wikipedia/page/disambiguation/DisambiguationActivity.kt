package org.wikipedia.page.disambiguation

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.view.ViewGroup
import androidx.activity.viewModels
import androidx.core.view.isVisible
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
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
import org.wikipedia.util.log.L
import org.wikipedia.views.DrawableItemDecoration
import org.wikipedia.views.PageItemView

class DisambiguationActivity : BaseActivity() {
    private lateinit var binding: ActivityDisambiguationBinding

    private val itemCallback = ItemCallback()
    private val viewModel: DisambiguationViewModel by viewModels()

    public override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDisambiguationBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setStatusBarColor(ResourceUtil.getThemedColor(this, android.R.attr.windowBackground))
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = getString(R.string.page_similar_titles)
        binding.root.setLayoutDirectionByLang(viewModel.wikiSite.languageCode)

        binding.disambiguationRecycler.layoutManager = LinearLayoutManager(this)
        binding.disambiguationRecycler.addItemDecoration(DrawableItemDecoration(this, R.attr.list_divider, drawStart = false, drawEnd = false))

        binding.disambiguationError.retryClickListener = View.OnClickListener { viewModel.loadPages() }
        binding.disambiguationError.backClickListener = View.OnClickListener { onBackPressedDispatcher.onBackPressed() }

        viewModel.similarPagesData.observe(this) {
            when (it) {
                is Resource.Loading -> {
                    binding.disambiguationProgress.isVisible = true
                    binding.disambiguationError.isVisible = false
                    binding.disambiguationRecycler.isVisible = false
                }
                is Resource.Success -> {
                    binding.disambiguationProgress.isVisible = false
                    binding.disambiguationError.isVisible = false
                    binding.disambiguationRecycler.isVisible = true
                    binding.disambiguationRecycler.adapter = DisambiguationAdapter(it.data)
                }
                is Resource.Error -> {
                    binding.disambiguationProgress.isVisible = false
                    binding.disambiguationRecycler.isVisible = false
                    binding.disambiguationError.setError(it.throwable)
                    binding.disambiguationError.isVisible = true
                    L.e(it.throwable)
                }
            }
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
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

    private inner class DisambiguationAdapter(val titles: List<PageTitle>) : RecyclerView.Adapter<DisambiguationItemHolder>() {
        override fun getItemCount(): Int {
            return titles.size
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): DisambiguationItemHolder {
            val view = PageItemView<PageTitle>(this@DisambiguationActivity)
            view.callback = itemCallback
            return DisambiguationItemHolder(view)
        }

        override fun onBindViewHolder(holder: DisambiguationItemHolder, position: Int) {
            holder.bindItem(titles[position])
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
