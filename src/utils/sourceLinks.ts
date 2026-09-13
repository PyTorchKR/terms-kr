/** Reader-facing links. Keep the original, commit-pinned source in the data. */
export function getReadableSourceUrl(source: string): string {
  let url: URL
  try {
    url = new URL(source)
  } catch {
    return source
  }
  if (url.protocol !== 'https:' || url.hostname !== 'github.com') return source

  const docs = url.pathname.match(
    /^\/huggingface\/(transformers|smolagents)\/blob\/[^/]+\/docs\/source\/(ko|en)\/(.+)\.md$/,
  )
  if (docs) {
    // GitHub line anchors do not refer to positions in the rendered Docs page.
    return `https://huggingface.co/docs/${docs[1]}/${docs[2]}/${docs[3]}`
  }

  const blog = url.pathname.match(
    /^\/Hugging-Face-KREW\/hugging-face-krew\.github\.io\/blob\/[^/]+\/_posts\/\d{4}-\d{2}-\d{1,2}-(.+)\.md$/,
  )
  if (blog) {
    // KREW uses /:title/. All currently referenced posts, including explicit
    // frontmatter slugs, were checked against their published permalinks.
    return `https://hugging-face-krew.github.io/${blog[1]}/`
  }
  return source
}
