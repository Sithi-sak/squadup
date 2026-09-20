/** Largest edge (in px) a chat image keeps after compression. The transcript renders a bubble a
 * few hundred px wide, and the backend re-encodes to WebP at 1920 anyway - this is about what
 * leaves the device, not what gets stored. */
const CHAT_IMAGE_MAX_DIMENSION = 1600

const CHAT_IMAGE_QUALITY = 0.8

/** Files already this small aren't worth a decode/re-encode round trip. */
const SKIP_COMPRESSION_BELOW_BYTES = 200 * 1024

export interface CompressImageOptions {
  maxDimension?: number
  quality?: number
  /** Output mime type. WebP is what the backend stores, and every browser this app targets can
   * encode it; anything else falls back to JPEG below. */
  type?: string
}

function canEncode(type: string) {
  const canvas = document.createElement('canvas')
  canvas.width = 1
  canvas.height = 1
  return canvas.toDataURL(type).startsWith(`data:${type}`)
}

async function loadBitmap(file: File) {
  if (typeof createImageBitmap === 'function') {
    // Decodes off the main thread and applies the EXIF orientation, so a portrait phone photo
    // doesn't land in the chat on its side.
    return createImageBitmap(file, { imageOrientation: 'from-image' })
  }
  const url = URL.createObjectURL(file)
  try {
    const img = new Image()
    await new Promise<void>((resolve, reject) => {
      img.onload = () => resolve()
      img.onerror = () => reject(new Error('Could not read that image'))
      img.src = url
    })
    return img
  } finally {
    URL.revokeObjectURL(url)
  }
}

/** Downscales and re-encodes an image before upload, so a multi-MB phone photo doesn't have to
 * travel the wire at full resolution just to be shown at bubble size. Returns the original file
 * untouched if it's already small, if it isn't a raster image, or if anything about the canvas
 * path fails - a failed compression should never be the reason a message can't be sent. */
export async function compressImage(file: File, options: CompressImageOptions = {}): Promise<File> {
  const {
    maxDimension = CHAT_IMAGE_MAX_DIMENSION,
    quality = CHAT_IMAGE_QUALITY,
    type = canEncode('image/webp') ? 'image/webp' : 'image/jpeg',
  } = options

  // GIFs would lose their animation, and SVGs aren't raster to begin with.
  if (
    !file.type.startsWith('image/') ||
    file.type === 'image/gif' ||
    file.type === 'image/svg+xml'
  ) {
    return file
  }
  if (file.size <= SKIP_COMPRESSION_BELOW_BYTES) return file

  try {
    const source = await loadBitmap(file)
    const width = 'naturalWidth' in source ? source.naturalWidth : source.width
    const height = 'naturalHeight' in source ? source.naturalHeight : source.height
    const scale = Math.min(1, maxDimension / Math.max(width, height))

    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(width * scale))
    canvas.height = Math.max(1, Math.round(height * scale))
    const ctx = canvas.getContext('2d')
    if (!ctx) return file
    ctx.imageSmoothingQuality = 'high'
    ctx.drawImage(source, 0, 0, canvas.width, canvas.height)
    if ('close' in source) source.close()

    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, type, quality))
    if (!blob || blob.size >= file.size) return file

    const extension = type === 'image/webp' ? 'webp' : 'jpg'
    const name = file.name.replace(/\.[^.]+$/, '') || 'image'
    return new File([blob], `${name}.${extension}`, { type, lastModified: Date.now() })
  } catch {
    return file
  }
}
