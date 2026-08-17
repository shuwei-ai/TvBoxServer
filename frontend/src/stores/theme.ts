import { defineStore } from 'pinia'
import { ref } from 'vue'
import { storage } from '@/utils/storage'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref<boolean>(storage.getTheme() === 'dark')

  function applyTheme() {
    const html = document.documentElement
    if (isDark.value) {
      html.classList.add('dark')
      storage.setTheme('dark')
    } else {
      html.classList.remove('dark')
      storage.setTheme('light')
    }
  }

  function toggleTheme() {
    isDark.value = !isDark.value
    applyTheme()
  }

  function initTheme() {
    applyTheme()
  }

  return {
    isDark,
    toggleTheme,
    initTheme
  }
})
