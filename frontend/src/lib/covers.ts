import { ref, type Ref } from 'vue'

const CDN_BASE = 'https://cdn.jsdelivr.net/gh/Sithi-sak/game-cover@main'
const TREE_API_URL = 'https://api.github.com/repos/Sithi-sak/game-cover/git/trees/main?recursive=1'
const MANIFEST_CACHE_KEY = 'squadup:cover-manifest:v2'
const MANIFEST_CACHE_TTL_MS = 60 * 60 * 1000

interface GitHubTreeEntry {
  path: string
  type: string
}

interface GitHubTreeResponse {
  tree: GitHubTreeEntry[]
}

// Cover folders hold a single, arbitrarily-numbered file (e.g. 004.webp, 027.webp),
// so the real filename per slug is looked up from the repo tree instead of assumed.
const coverFilenames: Ref<Map<string, string>> = ref(new Map())
let manifestPromise: Promise<void> | null = null

function readCachedManifest(): Map<string, string> | null {
  try {
    const raw = localStorage.getItem(MANIFEST_CACHE_KEY)
    if (!raw) return null
    const { timestamp, entries } = JSON.parse(raw) as { timestamp: number; entries: [string, string][] }
    if (Date.now() - timestamp > MANIFEST_CACHE_TTL_MS) return null
    return new Map(entries)
  } catch {
    return null
  }
}

function writeCachedManifest(map: Map<string, string>) {
  try {
    localStorage.setItem(
      MANIFEST_CACHE_KEY,
      JSON.stringify({ timestamp: Date.now(), entries: Array.from(map.entries()) }),
    )
  } catch {
    // storage unavailable or full — the manifest just won't be cached
  }
}

async function loadCoverManifest(): Promise<void> {
  const cached = readCachedManifest()
  if (cached) {
    coverFilenames.value = cached
    return
  }

  const res = await fetch(TREE_API_URL)
  if (!res.ok) return
  const data: GitHubTreeResponse = await res.json()

  const map = new Map<string, string>()
  for (const entry of data.tree) {
    if (entry.type !== 'blob') continue
    const match = entry.path.match(/^covers\/([^/]+)\/([^/]+)$/)
    const [, slug, filename] = match ?? []
    if (slug && filename) map.set(slug, filename)
  }

  coverFilenames.value = map
  writeCachedManifest(map)
}

export function useCoverManifest(): Ref<Map<string, string>> {
  if (!manifestPromise) {
    manifestPromise = loadCoverManifest()
  }
  return coverFilenames
}

export function gameCoverUrl(slug: string, filename: string): string {
  return `${CDN_BASE}/covers/${slug}/${filename}`
}
