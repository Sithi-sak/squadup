import { ref, type Ref } from 'vue'
import coverManifest from '@/data/coverManifest.json'

const CDN_BASE = 'https://cdn.jsdelivr.net/gh/Sithi-sak/game-cover@main'

// Cover folders hold a single, arbitrarily-numbered file (e.g. 004.webp), so the real filename
// per slug is baked into `data/coverManifest.json` instead of being looked up from the GitHub
// API at runtime. Regenerate it after adding/renaming a cover in the game-cover repo:
//   curl -s "https://api.github.com/repos/Sithi-sak/game-cover/git/trees/main?recursive=1" \
//     | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps({p[1]: p[2] for e in d['tree'] if e['type']=='blob' and len(p := e['path'].split('/')) == 3 and p[0]=='covers'}, indent=2, sort_keys=True))" \
//     > src/data/coverManifest.json
const coverFilenames: Ref<Map<string, string>> = ref(new Map(Object.entries(coverManifest)))

export function useCoverManifest(): Ref<Map<string, string>> {
  return coverFilenames
}

export function gameCoverUrl(slug: string, filename: string): string {
  return `${CDN_BASE}/covers/${slug}/${filename}`
}
