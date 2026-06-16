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
          style="position: relative; overflow: hidden; padding-bottom: 14px; padding-right: 28px;"
        >
          <!-- Кнопка закрытия (крестик) -->
          <button class="toast-close" @click="app.removeToast(t.id)">
            <i class="fas fa-times"></i>
          </button>

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
            <!-- Кнопка действия (скачать) -->
            <button
              v-if="t.action"
              class="toast-action"
              @click="t.action.callback(); app.removeToast(t.id);"
            >
              <i class="fas fa-download"></i> {{ t.action.label }}
            </button>
          </div>

          <!-- Глайдер (прогресс-бар загрузки) -->
          <div
            class="toast-progress"
            :style="{ animationDuration: (t.duration || 4000) + 'ms' }"
          ></div>
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
