<template>
  <el-dialog
    v-model="visible"
    title="绑定新 TVBox 设备"
    width="460px"
    destroy-on-close
    append-to-body
    class="custom-dialog"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-position="top"
      @submit.prevent="handleSubmit"
    >
      <el-form-item label="设备 ID (Device ID)" prop="device_id">
        <el-input
          v-model="formData.device_id"
          placeholder="例如：tvbox_living_room"
          clearable
        />
        <div class="field-hint">需与 TVBox 客户端中设置的设备唯一标识保持一致</div>
      </el-form-item>

      <el-form-item label="设备名称" prop="device_name">
        <el-input
          v-model="formData.device_name"
          placeholder="例如：客厅电视 / 卧室小米电视"
          clearable
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          立即绑定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useDeviceStore } from '@/stores'
import type { BindDeviceParams, BindDeviceResponse } from '@/types'

const emit = defineEmits<{
  (e: 'success', res: BindDeviceResponse): void
}>()

const deviceStore = useDeviceStore()
const visible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const formData = reactive<BindDeviceParams>({
  device_id: '',
  device_name: ''
})

const rules: FormRules = {
  device_id: [
    { required: true, message: '请输入设备 ID', trigger: 'blur' },
    { min: 3, message: '设备 ID 长度至少 3 个字符', trigger: 'blur' }
  ],
  device_name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' }
  ]
}

function open() {
  formData.device_id = ''
  formData.device_name = ''
  visible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      const res = await deviceStore.bindDevice(formData)
      ElMessage.success('设备绑定成功！')
      visible.value = false
      emit('success', res)
    } catch (err: any) {
      // 错误由 axios 拦截器提示
    } finally {
      submitting.value = false
    }
  })
}

defineExpose({
  open
})
</script>

<style scoped lang="scss">
.field-hint {
  font-size: 12px;
  color: var(--app-text-muted);
  margin-top: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
