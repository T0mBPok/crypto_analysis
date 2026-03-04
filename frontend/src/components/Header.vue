<template>
  <div class="header">
    <h1>🌐 Crypto Neo4j Graph</h1>
    <div class="controls">
      <!-- Кнопка управления тикерами -->
      <button 
        @click="$emit('toggle-manager')" 
        class="manager-btn"
        :class="{ active: showManager }"
        title="Управление тикерами"
      >
        📋 Тикеры
      </button>
      
      <input 
        v-model="localTicker" 
        placeholder="BTCUSDT" 
        style="width: 140px"
        @keyup.enter="$emit('load-ticker')"
      >
      <button 
        @click="$emit('load-ticker')" 
        :class="{ active: viewMode === 'ticker' }"
      >
        📍 Тикер
      </button>
      <button 
        @click="$emit('load-all')" 
        :class="{ active: viewMode === 'all' }"
      >
        🗺️ Все
      </button>
      
      <button @click="$emit('load-debug')" style="background:#ff6b6b">
        🐛 Debug
      </button>
      <button 
        @click="$emit('toggle-candles')" 
        :class="{ active: showCandles }"
      >
        📊 Свечи
      </button>
      <button @click="$emit('zoom', 1)">📏</button>
      <button @click="$emit('zoom', 1.2)">+</button>
      <button @click="$emit('zoom', 0.8)">-</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  ticker: String,
  viewMode: String,
  showCandles: Boolean,
  showManager: Boolean  // Новый проп
})

const emit = defineEmits([
  'update:ticker', 
  'load-ticker', 
  'load-all', 
  'load-debug', 
  'toggle-candles', 
  'toggle-manager',  // Новый эмит
  'zoom'
])

const localTicker = ref(props.ticker)

watch(() => props.ticker, (newVal) => {
  localTicker.value = newVal
})

watch(localTicker, (newVal) => {
  emit('update:ticker', newVal)
})
</script>

<style scoped>
.header { 
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
  padding: 1rem; 
  display: flex; 
  gap: 1rem; 
  align-items: center; 
  flex-wrap: wrap;
}
h1 { margin: 0; font-size: 1.4rem; }
.controls { 
  display: flex; 
  gap: 0.5rem; 
  flex-wrap: wrap; 
  align-items: center;
}
button, input { 
  padding: 0.6rem 1rem; 
  border: none; 
  border-radius: 8px; 
  background: rgba(255,255,255,0.15); 
  color: white; 
  font-size: 14px; 
  cursor: pointer; 
  backdrop-filter: blur(10px);
}
button:hover { background: rgba(255,255,255,0.25) !important; }
button.active { 
  background: #4ecdc4 !important; 
  color: #1a1a2e;
  font-weight: bold;
}
.manager-btn {
  background: #ffaa00 !important;
  color: #1a1a2e !important;
  font-weight: bold;
}
.manager-btn.active {
  background: #4ecdc4 !important;
}
input:focus { 
  outline: 2px solid #4ecdc4; 
  background: rgba(255,255,255,0.25); 
}
</style>