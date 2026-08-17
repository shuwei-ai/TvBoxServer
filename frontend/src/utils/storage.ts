const TOKEN_KEY = 'tvbox_jwt'
const USER_KEY = 'tvbox_user'
const THEME_KEY = 'tvbox_theme'

export const storage = {
  getToken(): string {
    return localStorage.getItem(TOKEN_KEY) || ''
  },
  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token)
  },
  removeToken(): void {
    localStorage.removeItem(TOKEN_KEY)
  },
  getUser<T = any>(): T | null {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as T
    } catch {
      return null
    }
  },
  setUser(user: any): void {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },
  removeUser(): void {
    localStorage.removeItem(USER_KEY)
  },
  getTheme(): string {
    return localStorage.getItem(THEME_KEY) || 'dark'
  },
  setTheme(theme: string): void {
    localStorage.setItem(THEME_KEY, theme)
  },
  clearAuth(): void {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }
}
