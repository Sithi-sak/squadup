import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { RealtimeChannel } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'

/** Who has SquadUp open right now, via Supabase Realtime Presence. Every signed-in tab joins
 * one shared channel keyed on its user id, so a user counts as online while any of their tabs
 * is connected and drops off when the last one closes (or its socket times out). Nothing is
 * stored, so there is no stale "online" left behind by a crashed tab. */
export const usePresenceStore = defineStore('presence', () => {
  const onlineIds = ref<Set<string>>(new Set())
  let channel: RealtimeChannel | null = null

  function isOnline(userId: string | null | undefined) {
    return !!userId && onlineIds.value.has(userId)
  }

  function unsubscribe() {
    if (channel) {
      supabase.removeChannel(channel)
      channel = null
    }
    onlineIds.value = new Set()
  }

  function subscribe(userId: string) {
    unsubscribe()
    const joined = supabase.channel('presence:online', {
      config: { presence: { key: userId } },
    })
    joined
      .on('presence', { event: 'sync' }, () => {
        onlineIds.value = new Set(Object.keys(joined.presenceState()))
      })
      .subscribe((status) => {
        if (status === 'SUBSCRIBED') void joined.track({ onlineAt: new Date().toISOString() })
      })
    channel = joined
  }

  return { onlineIds, isOnline, subscribe, unsubscribe }
})
