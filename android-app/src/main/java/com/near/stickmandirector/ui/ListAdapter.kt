package com.near.stickmandirector.ui

import android.content.Context
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView

/** Minimal RecyclerView adapter: rows are built programmatically by [build]. */
class ListAdapter<T>(private var items: List<T>, private val build: (Context, T) -> View) :
    RecyclerView.Adapter<ListAdapter.VH>() {
    class VH(val frame: FrameLayout) : RecyclerView.ViewHolder(frame)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH = VH(FrameLayout(parent.context).apply {
        layoutParams = RecyclerView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
    })

    override fun onBindViewHolder(holder: VH, position: Int) {
        holder.frame.removeAllViews()
        holder.frame.addView(build(holder.frame.context, items[position]))
    }

    override fun getItemCount(): Int = items.size

    @android.annotation.SuppressLint("NotifyDataSetChanged")
    fun submit(list: List<T>) { items = list; notifyDataSetChanged() }

    companion object {
        fun recycler(ctx: Context, adapter: RecyclerView.Adapter<*>): RecyclerView = RecyclerView(ctx).apply {
            layoutManager = LinearLayoutManager(ctx)
            this.adapter = adapter
            clipToPadding = false
            val p = Ui.dp(ctx, 12); setPadding(p, 0, p, p)
        }
    }
}
