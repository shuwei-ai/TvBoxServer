import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getDevicesApi, bindDeviceApi, unbindDeviceApi } from '@/api/devices'
import { resetApiKeyApi } from '@/api/apiKey'
import type { DeviceItem, ApiKeyInfo, BindDeviceParams } from '@/types'

export const useDeviceStore = defineStore('device', () => {
  const devices = ref<DeviceItem[]>([])
  const apiKeyInfo = ref<ApiKeyInfo | null>(null)
  const selectedDeviceId = ref<string>('') // '' means auto-route
  const loading = ref<boolean>(false)

  const onlineDevices = computed(() => devices.value.filter((d) => d.online))
  const deviceCount = computed(() => devices.value.length)
  const defaultDevice = computed(() => devices.value.find((d) => d.is_default) || devices.value[0])

  async function loadDevices() {
    loading.value = true
    try {
      const data = await getDevicesApi()
      devices.value = data.devices || []
      apiKeyInfo.value = data.api_key || null
      return data
    } finally {
      loading.value = false
    }
  }

  async function bindDevice(params: BindDeviceParams) {
    const res = await bindDeviceApi(params)
    await loadDevices()
    return res
  }

  async function unbindDevice(idOrDeviceId: string) {
    const target = devices.value.find((d) => d.id === idOrDeviceId || d.device_id === idOrDeviceId)
    const res = await unbindDeviceApi(idOrDeviceId)
    if (
      selectedDeviceId.value &&
      (selectedDeviceId.value === idOrDeviceId || (target && target.device_id === selectedDeviceId.value))
    ) {
      selectedDeviceId.value = ''
    }
    await loadDevices()
    return res
  }

  async function resetApiKey() {
    const res = await resetApiKeyApi()
    await loadDevices()
    return res
  }

  function setSelectedDeviceId(id: string) {
    selectedDeviceId.value = id
  }

  return {
    devices,
    apiKeyInfo,
    selectedDeviceId,
    loading,
    onlineDevices,
    deviceCount,
    defaultDevice,
    loadDevices,
    bindDevice,
    unbindDevice,
    resetApiKey,
    setSelectedDeviceId
  }
})
