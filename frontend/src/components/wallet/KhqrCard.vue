<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import QRCode from 'qrcode'
import { PhCheckCircle } from '@phosphor-icons/vue'
import abaPayLogo from '@/assets/payway/aba-pay.svg'
import khqrBadge from '@/assets/payway/khqr-badge.svg'

/**
 * 4.58, ported from Niyey. The KHQR payment display, laid out to ABA PayWay's QR display
 * guideline (`aba_resource/qr_guideline.png`, "on Website Popup"):
 * ABA PAY wordmark, then the KHQR card (red header with the KHQR wordmark
 * and folded corner, merchant and amount above a perforation line, the code
 * below with the Bakong badge over its middle), then the scan caption.
 *
 * Every size is the guideline's 1x measurement in `--u` units (196px card
 * and logo, 144px code, 24px safe space), so `scale` resizes the whole
 * display in proportion while everything stays drawn at full sharpness.
 */
const props = withDefaults(
  defineProps<{
    merchant: string
    /** US dollars, PayWay charges top-ups in USD. */
    amount: number
    payload: string
    /** Dims the QR and stamps it once the payment lands. */
    paid: boolean
    expired: boolean
    /** Multiple of the guideline's 1x size. */
    scale?: number
  }>(),
  { scale: 1 },
)

const canvas = ref<HTMLCanvasElement>()

/** Guideline 1x size of the code (its maximum). */
const QR_SIZE = 144

async function render() {
  if (!canvas.value) return
  // Drawn at 2x the displayed size so the modules stay sharp on a retina
  // screen and under a phone camera held up to the monitor.
  await QRCode.toCanvas(canvas.value, props.payload, {
    width: Math.round(QR_SIZE * props.scale * 2),
    margin: 0,
    // Highest level (~30% recoverable): the Bakong badge covers the
    // middle of the code, which banking apps have to read around.
    errorCorrectionLevel: 'H',
    color: { dark: '#000000', light: '#ffffff' },
  })
  // `toCanvas` writes its own inline width/height onto the element, which
  // outranks the stylesheet - clear them so the CSS size applies.
  canvas.value.style.removeProperty('width')
  canvas.value.style.removeProperty('height')
}

onMounted(render)
watch(() => [props.payload, props.scale], render)
</script>

<template>
  <div class="khqr-display" :style="{ '--u': `${scale}px` }">
    <img :src="abaPayLogo" alt="ABA PAY" class="aba-pay" />

    <div class="khqr-card">
      <div class="header">
        <!-- Wordmark traced from the KHQR card artwork. -->
        <svg class="logo" viewBox="177 46 87 21" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M194.859 67H190.271L180.768 57.1667V67H177V46H180.768V55.3333L189.944 46H194.367L184.537 56L194.859 67Z"
            fill="white"
          />
          <path
            d="M212.062 46H215.667V67H212.062V57.8333H201.576V67H197.808V46H201.576V54.8333H212.062V46Z"
            fill="white"
          />
          <path
            d="M233.525 53.8332V60.4999H226.972C226.316 60.4999 225.825 59.9999 225.825 59.3332V53.8332C225.825 53.1665 226.316 52.6665 226.972 52.6665H232.215C233.034 52.4999 233.525 53.1665 233.525 53.8332Z"
            fill="white"
          />
          <path
            d="M234.672 63.6667H224.842C223.695 63.6667 222.712 62.6667 222.712 61.5V51.5C222.712 50.3333 223.695 49.3333 224.842 49.3333H234.672C235.819 49.3333 236.802 50.3333 236.802 51.5V61.5L240.079 64.8333V49.1667C240.079 47.3333 238.604 46 236.966 46H222.712C220.909 46 219.599 47.5 219.599 49.1667V63.6667C219.599 65.5 221.073 66.8333 222.712 66.8333H237.949L234.672 63.6667Z"
            fill="white"
          />
          <path
            d="M264 56.5H260.723C260.723 52.5 257.61 49.3333 253.678 49.3333C250.565 49.3333 247.944 51.3333 246.96 54.3333C246.797 55 246.633 55.8333 246.633 56.5V67H246.469C244.667 67 243.356 65.5 243.356 63.8333V56.5C243.356 53.6667 244.503 50.8333 246.633 48.8333C248.599 47 251.057 46 253.678 46C259.412 46 264 50.6667 264 56.5Z"
            fill="white"
          />
          <path
            d="M264 66.9999H259.412L258.265 65.8333L255.808 63.3333L252.367 59.8333H256.955L264 66.9999Z"
            fill="white"
          />
        </svg>
      </div>

      <div class="details">
        <p class="merchant">{{ merchant }}</p>
        <p class="amount">$ {{ amount.toFixed(2) }}</p>
      </div>

      <div class="perforation" />

      <div class="qr" :class="{ 'qr--dim': paid || expired }">
        <canvas ref="canvas" class="qr-canvas" />
        <img v-if="!paid && !expired" :src="khqrBadge" alt="" class="badge" />
        <div v-if="paid" class="stamp">
          <PhCheckCircle :size="40 * scale" weight="fill" />
          <span>Payment received</span>
        </div>
        <div v-else-if="expired" class="stamp stamp--muted">
          <span>This QR has expired.</span>
        </div>
      </div>
    </div>

    <p class="caption">Scan with ABA Mobile or any KHQR supported banking app</p>
  </div>
</template>

<style scoped>
/* All sizes are guideline 1x pixels times --u. */
.khqr-display {
  --u: 1px;
  display: flex;
  flex-direction: column;
  align-items: center;
  /* Minimum safe space: 24 on every side. */
  padding: calc(var(--u) * 24);
  text-align: left;
}

/* ABA PAY logo at its guideline minimum, 196 x 31. */
.aba-pay {
  display: block;
  width: calc(var(--u) * 196);
  height: calc(var(--u) * 31);
}

.khqr-card {
  position: relative;
  width: calc(var(--u) * 196);
  margin-top: calc(var(--u) * 30);
  border-radius: calc(var(--u) * 12);
  background: #ffffff;
  box-shadow: 0 0 calc(var(--u) * 11) rgba(0, 0, 0, 0.16);
  overflow: hidden;
  flex-shrink: 0;
}

.header {
  position: relative;
  height: calc(var(--u) * 34);
  background: #e21a1a;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* The folded corner the KHQR header always carries on its right edge. */
.header::after {
  content: '';
  position: absolute;
  top: 100%;
  right: 0;
  width: calc(var(--u) * 16);
  height: calc(var(--u) * 16);
  background: #e21a1a;
  clip-path: polygon(0 0, 100% 0, 100% 100%);
}

.logo {
  width: calc(var(--u) * 43);
  height: calc(var(--u) * 10.4);
}

.details {
  padding: calc(var(--u) * 18) calc(var(--u) * 26) 0;
}

.merchant {
  margin: 0;
  font-size: calc(var(--u) * 11);
  line-height: 1.3;
  color: #1a1a1a;
}

/* Symbol and figure share one size and weight, as in "$ 40.00". */
.amount {
  margin: calc(var(--u) * 4) 0 0;
  font-size: calc(var(--u) * 19);
  line-height: 1.2;
  font-weight: 500;
  color: #000000;
}

.perforation {
  margin-top: calc(var(--u) * 14);
  border-top: 1px dashed rgba(0, 0, 0, 0.5);
}

.qr {
  position: relative;
  display: flex;
  justify-content: center;
  padding: calc(var(--u) * 22) 0 calc(var(--u) * 26);
}

/* Guideline code area: 100-144 square; drawn at the 144 maximum. */
.qr-canvas {
  display: block;
  width: calc(var(--u) * 144);
  height: calc(var(--u) * 144);
  transition: opacity 0.25s ease;
}

/* Fades the code itself, not the stamp - opacity on the wrapper would take
   the stamp down with it, since a child can't be more opaque than its parent. */
.qr--dim .qr-canvas {
  opacity: 0.1;
}

/* Bakong KHQR badge over the middle of the code, about a quarter of its width. */
.badge {
  position: absolute;
  top: calc(var(--u) * (22 + 72));
  left: 50%;
  width: calc(var(--u) * 38);
  height: calc(var(--u) * 38);
  transform: translate(-50%, -50%);
}

.stamp {
  position: absolute;
  top: calc(var(--u) * 22);
  left: 50%;
  width: calc(var(--u) * 144);
  height: calc(var(--u) * 144);
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: calc(var(--u) * 6);
  color: #059669;
  font-size: calc(var(--u) * 11);
  font-weight: 600;
  text-align: center;
}

.stamp--muted {
  color: #6b7280;
}

.caption {
  width: calc(var(--u) * 196);
  margin: calc(var(--u) * 20) 0 0;
  font-size: calc(var(--u) * 11);
  line-height: 1.45;
  text-align: center;
  color: #878787;
}
</style>
