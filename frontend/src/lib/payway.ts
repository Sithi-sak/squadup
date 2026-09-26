/**
 * 4.57, ported from Niyey.
 * ABA PayWay's card popup (`checkout2-0.js`). The plugin renders PayWay's
 * own card form in an iframe over the page - card details go straight to
 * PayWay, never through SquadUp - driven by a hidden form it expects to find
 * as `#aba_merchant_request`, targeting its `aba_webservice` iframe.
 *
 * The loader pulls in the real plugin (`checkout.prod.js`) on a 1s timer,
 * so `AbaPayway` only exists a moment after the script tag loads. Same
 * script for sandbox and production; the form's `action` decides which
 * PayWay environment is hit.
 *
 * The plugin declares it as a top-level `const AbaPayway`, which is a global
 * binding but not a `window` property - so it has to be read as a bare
 * identifier (guarded by `typeof`), never as `window.AbaPayway`.
 */

interface AbaPaywayPlugin {
  checkout: () => void
  /** Hides the popup in place - unlike `closeCheckout`, without reloading the page. */
  closeCheckoutByContinueUrl: () => void
}

declare const AbaPayway: AbaPaywayPlugin | undefined

function plugin(): AbaPaywayPlugin | undefined {
  return typeof AbaPayway === 'undefined' ? undefined : AbaPayway
}

// `hide-close=2` makes the popup's close button just hide it, instead of the
// plugin's default of reloading the whole page.
const PLUGIN_URL = 'https://checkout.payway.com.kh/plugins/checkout2-0.js?hide-close=2'

let loading: Promise<void> | null = null

function loadPlugin(): Promise<void> {
  if (plugin()) return Promise.resolve()
  if (loading) return loading

  loading = new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.src = PLUGIN_URL
    script.onerror = () => {
      loading = null
      reject(new Error('PayWay plugin failed to load'))
    }
    document.head.appendChild(script)

    const startedAt = Date.now()
    const waitForGlobal = setInterval(() => {
      if (plugin()) {
        clearInterval(waitForGlobal)
        resolve()
      } else if (Date.now() - startedAt > 15000) {
        clearInterval(waitForGlobal)
        loading = null
        reject(new Error('PayWay plugin did not initialise'))
      }
    }, 100)
  })
  return loading
}

/** Warms the plugin up ahead of time so the popup opens without a wait. */
export function preloadPayWay() {
  loadPlugin().catch(() => {})
}

let stopWatchingClose: (() => void) | null = null

/**
 * Calls `onClose` once PayWay's popup goes away - the plugin gives no event
 * for it, so this watches its `#aba-checkout` container, which the plugin
 * empties or hides when the customer closes the popup (and when
 * `closePayWayCheckout` takes it down).
 */
function watchForClose(onClose: () => void) {
  stopWatchingClose?.()
  const container = document.getElementById('aba-checkout')
  if (!container) return

  // The popup's content goes in a moment after `checkout()`, so only an
  // emptying that follows it counts as a close.
  let opened = false
  const observer = new MutationObserver(() => {
    const visible = container.childElementCount > 0 && container.style.display !== 'none'
    if (visible) {
      opened = true
    } else if (opened) {
      stop()
      onClose()
    }
  })
  const stop = () => {
    observer.disconnect()
    if (stopWatchingClose === stop) stopWatchingClose = null
  }
  observer.observe(container, { childList: true, attributes: true, attributeFilter: ['style', 'class'] })
  stopWatchingClose = stop
}

/**
 * Opens PayWay's card popup for the signed fields the backend returned;
 * `onClose` runs when it's dismissed (cancelled, or taken down after paying).
 */
export async function openPayWayCheckout(signedFields: Record<string, string>, onClose: () => void) {
  await loadPlugin()

  const { form_url: action, ...fields } = signedFields
  document.getElementById('aba_merchant_request')?.remove()

  const form = document.createElement('form')
  form.id = 'aba_merchant_request'
  form.method = 'POST'
  form.target = 'aba_webservice'
  form.action = action ?? ''
  form.style.display = 'none'
  for (const [name, value] of Object.entries(fields)) {
    const input = document.createElement('input')
    input.type = 'hidden'
    input.name = name
    input.value = value
    form.appendChild(input)
  }
  document.body.appendChild(form)

  watchForClose(onClose)
  plugin()!.checkout()
}

/** Takes PayWay's popup down (if it's up) without the reload its own close does. */
export function closePayWayCheckout() {
  if (document.getElementById('aba-checkout')?.childElementCount) {
    plugin()?.closeCheckoutByContinueUrl()
  }
}
