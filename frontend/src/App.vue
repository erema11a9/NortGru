<template>
  <RouterView />

  <!-- Toast уведомления -->
  <Teleport to="body">
    <div class="toast-stack">
      <TransitionGroup name="toast">
        <div
          v-for="t in app.toasts"
          :key="t.id"
          :class="['toast', 'tw-' + t.type]"
        >
          <i
            :class="[
              'fas',
              t.type === 'ok'   ? 'fa-check-circle tg' :
              t.type === 'warn' ? 'fa-exclamation-triangle ty' :
              t.type === 'err'  ? 'fa-times-circle tr2' :
                                  'fa-info-circle tb'
            ]"
            style="font-size:18px;margin-top:1px;flex-shrink:0;"
          ></i>
          <div>
            <div class="toast-t">{{ t.title }}</div>
            <div class="toast-m">{{ t.message }}</div>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { RouterView } from 'vue-router'
import { useAppStore } from '@/stores/app'
const app = useAppStore()
</script>
