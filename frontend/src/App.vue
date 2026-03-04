<template>
  <div class="app">
    <Header 
      v-model:ticker="ticker"
      :view-mode="viewMode"
      :show-candles="showCandles"
      :strength-filter="strengthFilter"
      :threshold="threshold"
      :show-manager="showTickerManager"
      @load-ticker="loadTicker"
      @load-all="loadAll"
      @load-debug="loadDebug"
      @toggle-candles="toggleCandles"
      @toggle-manager="showTickerManager = !showTickerManager"
      @update:filters="updateFilters"
      @zoom="zoom"
    />
    
    <div id="graph-container">
      <div id="cy" ref="cyContainer"></div>
      
      <!-- Панель фильтров (для быстрого доступа) -->
      <div class="filters-panel" v-if="viewMode === 'all'">
        <div class="filter-group">
          <label>Сила связи:</label>
          <select v-model="strengthFilter" @change="applyFilters">
            <option value="">Все</option>
            <option value="STRONG">🔥 Сильные (>0.7)</option>
            <option value="MODERATE">⚡ Средние (0.4-0.7)</option>
            <option value="WEAK">💧 Слабые (<0.4)</option>
          </select>
        </div>
        <div class="filter-group">
          <label>Порог:</label>
          <input 
            type="range" 
            v-model.number="threshold" 
            min="0" 
            max="1" 
            step="0.05"
            @change="applyFilters"
          >
          <span>{{ threshold.toFixed(2) }}</span>
        </div>
        <button @click="applyFilters" class="apply-btn">Применить</button>
        <button @click="calculateAll" class="calc-btn">🧮 Рассчитать все</button>
        <div class="layout-controls">
          <button @click="applyRelayout" class="layout-btn" title="Перераспределить узлы">
            🔄 Перераспределить
          </button>
          <button @click="applyCircleLayout" class="layout-btn" title="Круговой layout">
            ⭕ Круг
          </button>
          <button @click="applyGridLayout" class="layout-btn" title="Сетка">
            🔲 Сетка
          </button>
        </div>
      </div>
      
      <div class="status">
        <div>📊 {{ nodesCount }} тикеров</div>
        <div>🔗 {{ edgesCount }} связей</div>
        <div v-if="viewMode === 'all' && correlationsCount">
          📈 {{ correlationsCount }} корреляций
        </div>
        <div>{{ status }}</div>
      </div>
      
      <InfoPanel 
        v-if="selectedElement" 
        :element="selectedElement"
        :loading="loadingCorrelation"
      />
      
      <CandlesPanel 
        v-model:show="showCandles"
        :ticker="selectedTicker"
        :candles="candles"
        :max-price="maxPrice"
      />

      <TickerManager 
        v-model:show="showTickerManager"
        @tickers-updated="refreshData"
      />

      <div v-if="loading" class="loading">⏳ {{ loadingMsg }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import Header from './components/Header.vue'
import InfoPanel from './components/InfoPanel.vue'
import CandlesPanel from './components/CandlesPanel.vue'
import TickerManager from './components/TickerManager.vue'
import { useCytoscape } from './composables/useCytoscape'
import api from './api'
import helpers from './utils/helpers'

// Состояние
const ticker = ref('BTCUSDT')
const viewMode = ref('all')
const showCandles = ref(false)
const loading = ref(false)
const loadingCorrelation = ref(false)
const loadingMsg = ref('')
const status = ref('Кликни кнопку!')
const nodesCount = ref(0)
const edgesCount = ref(0)
const correlationsCount = ref(0)
const selectedElement = ref(null)
const selectedTicker = ref(null)
const candles = ref([])
const maxPrice = ref(0)
const showTickerManager = ref(false)

// Фильтры
const strengthFilter = ref('')
const threshold = ref(0.0)

// Хранилище данных
const allCorrelations = ref([])
const nodesMap = ref(new Map())
const correlationsCache = ref(new Map())

// Cytoscape
const { cy, relayout, layoutCircle, layoutGrid, initCy, renderGraph, zoom: cyZoom } = useCytoscape()

// Применение фильтров
const applyFilters = async () => {
  if (viewMode.value === 'all') {
    await loadAllWithFilters()
  } else {
    await loadTicker()
  }
}

const refreshData = () => {
  if (viewMode.value === 'all') {
    loadAllWithFilters()
  } else {
    loadTicker()
  }
}

// Обновление фильтров из Header
const updateFilters = (filters) => {
  strengthFilter.value = filters.strength
  threshold.value = filters.threshold
  applyFilters()
}

const applyRelayout = () => {
  relayout()  // вызываем метод из useCytoscape
  status.value = 'Перераспределяю узлы...'
  setTimeout(() => {
    status.value = 'Готово'
  }, 2000)
}

const applyCircleLayout = () => {
  layoutCircle()  // вызываем метод из useCytoscape
  status.value = 'Круговой layout...'
  setTimeout(() => {
    status.value = 'Готово'
  }, 1500)
}

const applyGridLayout = () => {
  layoutGrid()  // вызываем метод из useCytoscape
  status.value = 'Сетка...'
  setTimeout(() => {
    status.value = 'Готово'
  }, 1500)
}

// Загрузка всех данных с фильтрами
const loadAllWithFilters = async () => {
  viewMode.value = 'all'
  loading.value = true
  loadingMsg.value = 'Загружаю данные...'
  
  try {
    // Загружаем граф (тикеры)
    const graphData = await api.getFullGraph()
    
    // Загружаем все корреляции с фильтрами
    const correlations = await api.getAllCorrelations(
      null, 
      threshold.value, 
      strengthFilter.value || null,
      'pearson'
    )
    
    allCorrelations.value = correlations
    correlationsCount.value = correlations.length
    
    // Создаем карту узлов
    nodesMap.value.clear()
    graphData.nodes.forEach(n => nodesMap.value.set(n.id, n))
    
    // Рендерим граф с корреляциями
    renderGraphWithCorrelations(graphData, correlations)
    
    status.value = `Загружено ${graphData.nodes.length} тикеров, ${correlations.length} связей`
  } catch(e) {
    status.value = `❌ ${e.message}`
  }
  loading.value = false
}

// Рендеринг с корреляциями
// Рендеринг с корреляциями
const renderGraphWithCorrelations = (graphData, correlations) => {
  const elements = []
  
  // Добавляем узлы
  graphData.nodes.forEach(n => elements.push({ data: n }))
  
  // Создаем карту корреляций для быстрого доступа
  const corrMap = new Map()
  correlations.forEach(c => {
    const key = [c.symbol1, c.symbol2].sort().join('-')
    corrMap.set(key, c)
  })
  
  // 🔥 Используем ребра из graphData, обогащая их данными из корреляций
  graphData.edges.forEach(edge => {
    const key = [edge.source, edge.target].sort().join('-')
    const corr = corrMap.get(key) || {}
    const pearson = corr.pearson || 0
    
    elements.push({
      data: {
        id: key,
        source: edge.source,
        target: edge.target,
        label: pearson ? pearson.toFixed(2) : '',
        width: helpers.getCorrelationWidth(pearson),
        color: helpers.getCorrelationColor(pearson),
        pearson: pearson,
        spearman: corr.spearman || 0,
        returns_corr: corr.returns_corr || 0,
        strength: corr.strength || helpers.getStrength(pearson),
        data_points: corr.data_points || 0,
        calculated_at: corr.calculated_at || null
      }
    })
  })
  
  // Рендерим
  cy.value.elements().remove()
  cy.value.add(elements)
  cy.value.layout({ name: 'cose', animate: true }).run()
  cy.value.fit(undefined, 60)
  
  nodesCount.value = graphData.nodes.length
  edgesCount.value = elements.filter(el => el.data.source).length
}

// Загрузка по тикеру (оставляем как есть, но используем фильтры)
const loadTicker = async () => {
  viewMode.value = 'ticker'
  loading.value = true
  loadingMsg.value = `Фокус: ${ticker.value}`
  
  try {
    const graphData = await api.getGraph(ticker.value)
    graphData.edges = helpers.filterDuplicateEdges(graphData.edges)
    
    let correlations = []
    try {
      const corrData = await api.getCorrelations(ticker.value, threshold.value)
      correlations = corrData.map(c => ({
        pair: c.symbol1 === ticker.value ? c.symbol2 : c.symbol1,
        symbol1: c.symbol1,
        symbol2: c.symbol2,
        ...c
      }))
      
      correlations.forEach(c => {
        const key = [c.symbol1, c.symbol2].sort().join('-')
        correlationsCache.value.set(key, c)
      })
    } catch(e) {
      console.log('Нет данных о корреляциях')
    }
    
    // Используем тот же метод рендеринга
    renderGraphWithCorrelations(graphData, correlations)
    status.value = `Фокус: ${ticker.value}`
    
    if (showCandles.value) {
      loadCandles(ticker.value)
    }
  } catch(e) {
    status.value = `❌ ${ticker.value} не найден`
  }
  loading.value = false
}

// Загрузка всех (без фильтров, для совместимости)
const loadAll = async () => {
  strengthFilter.value = ''
  threshold.value = 0
  await loadAllWithFilters()
}

// Расчет всех корреляций
const calculateAll = async () => {
  if (!confirm('Это может занять много времени. Продолжить?')) return
  
  loading.value = true
  loadingMsg.value = 'Рассчитываю корреляции...'
  
  try {
    const result = await api.calculateAllCorrelations('spot', 60, 30, 50)
    console.log('Результат расчета:', result)
    status.value = `✅ Рассчитано ${result.total_pairs} пар`
    
    // Перезагружаем данные
    await loadAllWithFilters()
  } catch(e) {
    status.value = `❌ Ошибка расчета: ${e.message}`
  }
  loading.value = false
}

// Загрузка данных для конкретной пары
const loadPairCorrelation = async (symbol1, symbol2) => {
  const key = [symbol1, symbol2].sort().join('-')
  
  if (correlationsCache.value.has(key)) {
    return correlationsCache.value.get(key)
  }
  
  try {
    loadingCorrelation.value = true
    const data = await api.getCorrelationBetween(symbol1, symbol2)
    correlationsCache.value.set(key, data)
    return data
  } catch(e) {
    console.error('Ошибка загрузки корреляции:', e)
    return null
  } finally {
    loadingCorrelation.value = false
  }
}

const loadCandles = async (symbol) => {
  if (!symbol) return
  
  try {
    loading.value = true
    loadingMsg.value = `Загрузка свечей для ${symbol}...`
    
    const data = await api.getCandles(symbol)
    
    if (Array.isArray(data) && data.length > 0) {
      candles.value = data
      maxPrice.value = Math.max(...data.map(c => c.close))
    } else {
      candles.value = []
    }
  } catch(e) {
    console.error('Ошибка загрузки свечей:', e)
    candles.value = []
  } finally {
    loading.value = false
  }
}

const loadDebug = async () => {
  loading.value = true
  loadingMsg.value = 'Debug БД...'
  
  try {
    const debug = await api.getDebug()
    console.table(debug.nodes)
    console.table(debug.edges)
    status.value = '🔍 Debug в консоли F12'
  } catch(e) {
    status.value = 'Debug недоступен'
  }
  loading.value = false
}

const toggleCandles = () => {
  showCandles.value = !showCandles.value
  if (showCandles.value && selectedTicker.value) {
    loadCandles(selectedTicker.value)
  }
}

const zoom = (factor) => {
  cyZoom(factor)
}

// Обработчик клика на ребро
const handleEdgeClick = async (edge) => {
  const source = edge.data('source')
  const target = edge.data('target')
  
  selectedElement.value = {
    type: 'edge',
    label: `${source} ↔ ${target}`,
    source,
    target,
    ...edge.data()
  }
}

// Инициализация
onMounted(() => {
  initCy({
    onNodeClick: (node) => {
      ticker.value = node.id()
      selectedTicker.value = node.id()
      selectedElement.value = {
        type: 'node',
        id: node.id(),
        label: node.data('label')
      }
      
      if (showCandles.value) {
        loadCandles(selectedTicker.value)
      }
    },
    onEdgeClick: handleEdgeClick,
    onBackgroundClick: () => {
      selectedElement.value = null
    }
  })
  
  setTimeout(() => loadAll(), 800)
})
</script>

<style scoped>
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

#graph-container {
  flex: 1;
  position: relative;
  background: radial-gradient(circle, #1a1a2e 0%, #16213e 100%);
}

#cy {
  width: 100%;
  height: 100%;
}

.filters-panel {
  position: absolute;
  top: 15px;
  left: 15px;
  background: rgba(0,0,0,0.85);
  padding: 1rem;
  border-radius: 12px;
  backdrop-filter: blur(10px);
  border: 1px solid #4ecdc4;
  z-index: 15;
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.layout-controls {
  display: flex;
  gap: 0.3rem;
  margin-left: 0.5rem;
}

.layout-btn {
  background: rgba(78, 205, 196, 0.3);
  color: #4ecdc4;
  border: 1px solid #4ecdc4;
  padding: 0.3rem 0.5rem;
  font-size: 12px;
}

.layout-btn:hover {
  background: #4ecdc4;
  color: #1a1a2e;
}

.ticker-manager-btn {
  position: absolute;
  top: 15px;
  left: 15px;
  width: 50px;
  height: 50px;
  border-radius: 25px;
  background: #4ecdc4;
  border: none;
  color: #1a1a2e;
  font-size: 1.5rem;
  cursor: pointer;
  z-index: 20;
  box-shadow: 0 2px 10px rgba(0,0,0,0.3);
  transition: all 0.2s;
}

.ticker-manager-btn:hover {
  transform: scale(1.1);
  background: #ffaa00;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #fff;
  font-size: 13px;
}

.filter-group select, .filter-group input {
  background: rgba(255,255,255,0.15);
  border: none;
  color: white;
  padding: 0.3rem;
  border-radius: 4px;
}

.apply-btn {
  background: #4ecdc4;
  color: #1a1a2e;
  font-weight: bold;
  padding: 0.3rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.calc-btn {
  background: #ffaa00;
  color: #1a1a2e;
  font-weight: bold;
  padding: 0.3rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.status {
  position: absolute;
  top: 15px;
  right: 15px;
  background: rgba(0,0,0,0.85);
  padding: 1rem;
  border-radius: 12px;
  font-size: 13px;
  min-width: 140px;
  text-align: center;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1);
  z-index: 10;
}

.loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%,-50%);
  font-size: 20px;
  color: #4ecdc4;
  font-weight: bold;
  z-index: 20;
}
</style>