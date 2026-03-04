<template>
  <div class="candles-panel" :class="{ visible: show }">
    <h3>
      📈 {{ ticker }}
      <button class="close-btn" @click="$emit('update:show', false)">×</button>
    </h3>
    <div v-if="candles.length === 0">Нет данных о свечах</div>
    <div class="mini-chart" v-else>
      <div v-for="c in candles.slice(-30)" 
           class="mini-candle" 
           :class="{ red: c.close < c.open }"
           :style="{ height: (c.close / maxPrice * 100) + '%' }"
           :title="formatCandleTooltip(c)">
      </div>
    </div>
    <div style="margin-top: 0.5rem; font-size: 11px; color: #888;">
      Последние 30 свечей (60min)
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: Boolean,
  ticker: String,
  candles: Array,
  maxPrice: Number
})

defineEmits(['update:show'])

const formatCandleTooltip = (c) => {
  return `${new Date(c.start).toLocaleString()}\nO: ${c.open.toFixed(2)}\nH: ${c.high.toFixed(2)}\nL: ${c.low.toFixed(2)}\nC: ${c.close.toFixed(2)}`
}
</script>

<style scoped>
.candles-panel {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: rgba(0,0,0,0.9);
  border-radius: 12px;
  padding: 1rem;
  width: 400px;
  backdrop-filter: blur(10px);
  border: 1px solid #4ecdc4;
  display: none;
  z-index: 1000;
}
.candles-panel.visible {
  display: block;
}
h3 {
  color: #4ecdc4;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.close-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0 5px;
}
.mini-chart {
  height: 150px;
  display: flex;
  align-items: flex-end;
  gap: 2px;
  margin-top: 1rem;
}
.mini-candle {
  flex: 1;
  background: #4ecdc4;
  min-height: 2px;
  transition: height 0.2s;
}
.mini-candle.red {
  background: #ff6b6b;
}
</style>