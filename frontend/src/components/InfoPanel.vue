<!-- src/components/InfoPanel.vue -->
<template>
  <div class="info-panel">
    <h3>{{ element.label }}</h3>
    
    <div v-if="loading" class="loading-spinner">
      ⏳ Загрузка данных...
    </div>
    
    <table v-else-if="element.type === 'edge'">
      <tr>
        <td>Корреляция Пирсона:</td>
        <td :class="'strength-' + element.strength">
          {{ element.pearson?.toFixed(3) }}
        </td>
      </tr>
      <tr>
        <td>Корреляция Спирмена:</td>
        <td>{{ element.spearman?.toFixed(3) }}</td>
      </tr>
      <tr>
        <td>Корреляция доходностей:</td>
        <td>{{ element.returns_corr?.toFixed(3) }}</td>
      </tr>
      <tr>
        <td>Точек данных:</td>
        <td>{{ element.data_points }}</td>
      </tr>
      <tr>
        <td>Сила:</td>
        <td :class="'strength-' + element.strength">
          {{ element.strength }}
        </td>
      </tr>
      <tr>
        <td>Расчитано:</td>
        <td>{{ formatDate(element.calculated_at) }}</td>
      </tr>
    </table>
    <div v-else>
      <div>Тикер: {{ element.id }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  element: Object,
  loading: Boolean
})

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU', { 
    day: '2-digit', 
    month: '2-digit',
    hour: '2-digit', 
    minute: '2-digit' 
  })
}
</script>

<style scoped>
.info-panel {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(0,0,0,0.9);
  border-radius: 12px;
  padding: 1rem;
  max-width: 300px;
  backdrop-filter: blur(10px);
  border: 1px solid #4ecdc4;
  pointer-events: none;
  z-index: 1000;
}
h3 {
  color: #4ecdc4;
  margin-bottom: 0.5rem;
  font-size: 1rem;
}
table {
  width: 100%;
  font-size: 12px;
}
td {
  padding: 2px 0;
}
td:first-child {
  color: #888;
  width: 60%;
}
td:last-child {
  text-align: right;
  font-weight: bold;
}
.strength-STRONG { color: #00ff88; }
.strength-MODERATE { color: #ffaa00; }
.strength-WEAK { color: #ff6b6b; }
.loading-spinner {
  text-align: center;
  padding: 1rem;
  color: #4ecdc4;
}
</style>