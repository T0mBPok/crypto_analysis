<!-- src/components/TickerManager.vue -->
<template>
  <div class="ticker-manager" :class="{ visible: show }">
    <div class="manager-overlay" @click="$emit('update:show', false)"></div>
    <div class="manager-window">
      <div class="manager-header">
        <h3>📋 Управление тикерами</h3>
        <button class="close-btn" @click="$emit('update:show', false)">×</button>
      </div>
      
      <div class="manager-content">
        <!-- Поиск на Bybit -->
        <div class="section">
          <h4>🔍 Поиск на Bybit</h4>
          <div class="search-box">
            <input 
              v-model="searchQuery" 
              placeholder="Введите символ (оставьте пустым для всех тикеров)"
              @keyup.enter="searchBybit"
            >
            <button @click="searchBybit" :disabled="searchLoading">
              {{ searchLoading ? 'Поиск...' : 'Найти' }}
            </button>
          </div>
          <div class="search-hint" v-if="!searchQuery">
            ⚡ Если оставить поле пустым, загрузятся ВСЕ тикеры с Bybit
          </div>
          
          <!-- Результаты поиска -->
          <div v-if="searchResults.length > 0" class="search-results">
            <div class="results-header" v-if="searchResults.length > 20">
              Найдено {{ searchResults.length }} тикеров. Показаны первые 50.
            </div>
            <div v-for="ticker in paginatedResults" :key="ticker.symbol" class="result-item">
              <span class="symbol">{{ ticker.symbol }}</span>
              <button 
                @click="addTicker(ticker.symbol)"
                :disabled="isTickerExists(ticker.symbol)"
                class="add-btn"
              >
                {{ isTickerExists(ticker.symbol) ? '✓ Добавлен' : '+' }}
              </button>
            </div>
            <div class="results-footer" v-if="hasMoreResults">
              <button @click="showMoreResults" class="more-btn">
                Показать еще 50 ({{ remainingResults }} осталось)
              </button>
            </div>
          </div>
        </div>
        
        <!-- Ручное добавление -->
        <div class="section">
          <h4>✏️ Ручное добавление</h4>
          <div class="manual-add">
            <input 
              v-model="manualSymbol" 
              placeholder="BTCUSDT"
              @keyup.enter="addManualTicker"
            >
            <button @click="addManualTicker" :disabled="!manualSymbol">
              Добавить
            </button>
          </div>
        </div>
        
        <!-- Массовое добавление -->
        <div class="section">
          <h4>📦 Массовое добавление</h4>
          <textarea 
            v-model="bulkSymbols" 
            placeholder="BTCUSDT&#10;ETHUSDT&#10;SOLUSDT"
            rows="4"
          ></textarea>
          <div class="bulk-actions">
            <button @click="addBulkTickers" :disabled="!bulkSymbols.trim()">
              Добавить все
            </button>
          </div>
        </div>
        
        <!-- Существующие тикеры -->
        <div class="section">
          <h4>📊 Тикеры в базе ({{ existingTickers.length }})</h4>
          <div class="ticker-list">
            <div v-for="ticker in existingTickers" :key="ticker.symbol" class="ticker-item">
              <span class="symbol">{{ ticker.symbol }}</span>
              <div class="ticker-actions">
                <button 
                  @click="loadCandlesForTicker(ticker.symbol)" 
                  class="action-btn"
                  title="Загрузить свечи"
                >
                  📊
                </button>
                <button 
                  @click="calculateCorrelationsForTicker(ticker.symbol)" 
                  class="action-btn"
                  title="Рассчитать корреляции"
                >
                  📈
                </button>
                <button 
                  @click="deleteTicker(ticker.symbol)" 
                  class="action-btn delete"
                  title="Удалить"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Статус бар -->
      <div v-if="statusMessage" class="status-bar" :class="statusType">
        {{ statusMessage }}
        <button @click="statusMessage = ''" class="status-close">×</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['update:show', 'tickers-updated'])

// Состояние
const searchQuery = ref('')
const searchLoading = ref(false)
const searchResults = ref([])

// Пагинация для результатов
const resultsPage = ref(1)
const RESULTS_PER_PAGE = 50

const paginatedResults = computed(() => {
  return searchResults.value.slice(0, resultsPage.value * RESULTS_PER_PAGE)
})

const hasMoreResults = computed(() => {
  return paginatedResults.value.length < searchResults.value.length
})

const remainingResults = computed(() => {
  return searchResults.value.length - paginatedResults.value.length
})

const manualSymbol = ref('')

const bulkSymbols = ref('')

const existingTickers = ref([])
const statusMessage = ref('')
const statusType = ref('info') // info, success, error

// Загрузка существующих тикеров
const loadExistingTickers = async () => {
  try {
    const tickers = await api.getAllTickers()
    existingTickers.value = tickers
  } catch (e) {
    showStatus('Ошибка загрузки тикеров', 'error')
  }
}

// Поиск на Bybit
const searchBybit = async () => {
  searchLoading.value = true
  resultsPage.value = 1
  
  try {
    let data
    if (searchQuery.value.trim()) {
      // Поиск по конкретному символу
      data = await api.searchBybitTickers('spot', searchQuery.value)
    } else {
      // Получение всех тикеров
      data = await api.searchBybitTickers('spot', '')
    }
    
    if (data && data.list) {
      searchResults.value = data.list.map(item => ({
        symbol: item.symbol
      }))
      showStatus(`Найдено ${data.list.length} тикеров`, 'success')
    } else {
      searchResults.value = []
      showStatus('Ничего не найдено', 'info')
    }
  } catch (e) {
    showStatus('Ошибка поиска', 'error')
    console.error(e)
  } finally {
    searchLoading.value = false
  }
}

// Показать еще результаты
const showMoreResults = () => {
  resultsPage.value++
}

// Проверка существования тикера
const isTickerExists = (symbol) => {
  return existingTickers.value.some(t => t.symbol === symbol)
}

// Добавление тикера
const addTicker = async (symbol) => {
  try {
    await api.addTickersBatch([symbol], 'spot')
    showStatus(`Тикер ${symbol} добавлен`, 'success')
    await loadExistingTickers()
    emit('tickers-updated')
    
    // Автоматически загружаем свечи и рассчитываем корреляции
    await Promise.all([
      loadCandlesForTicker(symbol),
      calculateCorrelationsForTicker(symbol)
    ])
  } catch (e) {
    showStatus(`Ошибка добавления ${symbol}`, 'error')
  }
}

// Ручное добавление
const addManualTicker = async () => {
  if (!manualSymbol.value.trim()) return
  await addTicker(manualSymbol.value.toUpperCase())
  manualSymbol.value = ''
}

// Массовое добавление
const addBulkTickers = async () => {
  const symbols = bulkSymbols.value
    .split('\n')
    .map(s => s.trim().toUpperCase())
    .filter(s => s && !isTickerExists(s))
  
  if (symbols.length === 0) {
    showStatus('Нет новых тикеров для добавления', 'info')
    return
  }
  
  try {
    await api.addTickersBatch(symbols, 'spot')
    showStatus(`Добавлено ${symbols.length} тикеров`, 'success')
    await loadExistingTickers()
    emit('tickers-updated')
    
    // Загружаем свечи и корреляции для новых тикеров
    for (const symbol of symbols) {
      await Promise.all([
        loadCandlesForTicker(symbol),
        calculateCorrelationsForTicker(symbol)
      ])
    }
    
    bulkSymbols.value = ''
  } catch (e) {
    showStatus('Ошибка массового добавления', 'error')
  }
}

// Загрузка свечей для тикера
const loadCandlesForTicker = async (symbol) => {
  try {
    await api.pullCandlesForTicker('spot', symbol, 4, 60)
    showStatus(`Свечи для ${symbol} загружены`, 'success')
  } catch (e) {
    showStatus(`Ошибка загрузки свечей для ${symbol}`, 'error')
  }
}

// Расчет корреляций для тикера
const calculateCorrelationsForTicker = async (symbol) => {
  try {
    // Получаем все существующие тикеры
    const tickers = existingTickers.value.map(t => t.symbol)
    const otherTickers = tickers.filter(s => s !== symbol)
    
    if (otherTickers.length === 0) return
    
    // Рассчитываем корреляции с каждым тикером
    let calculated = 0
    for (const other of otherTickers) {
      try {
        await api.calculateCorrelation(symbol, other, 'spot', 60, 30)
        calculated++
      } catch (e) {
        console.log(`Ошибка расчета ${symbol}-${other}`)
      }
    }
    
    showStatus(`Рассчитано ${calculated} корреляций для ${symbol}`, 'success')
  } catch (e) {
    showStatus(`Ошибка расчета корреляций для ${symbol}`, 'error')
  }
}

// Удаление тикера
const deleteTicker = async (symbol) => {
  if (!confirm(`Удалить тикер ${symbol}?`)) return
  
  try {
    await api.deleteTicker(symbol)
    showStatus(`Тикер ${symbol} удален`, 'success')
    await loadExistingTickers()
    emit('tickers-updated')
  } catch (e) {
    showStatus(`Ошибка удаления ${symbol}`, 'error')
  }
}

// Показ статуса
const showStatus = (message, type = 'info') => {
  statusMessage.value = message
  statusType.value = type
  setTimeout(() => {
    statusMessage.value = ''
  }, 3000)
}

onMounted(() => {
  loadExistingTickers()
})
</script>

<style scoped>
.ticker-manager {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: none;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.ticker-manager.visible {
  display: flex;
}

.manager-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
}

.manager-window {
  position: relative;
  width: 800px;
  max-width: 90vw;
  max-height: 85vh;
  background: rgba(20, 30, 50, 0.98);
  backdrop-filter: blur(20px);
  border: 2px solid #4ecdc4;
  border-radius: 24px;
  display: flex;
  flex-direction: column;
  z-index: 2001;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
  color: #fff;
}

.manager-header {
  padding: 1.5rem;
  border-bottom: 1px solid rgba(78, 205, 196, 0.3);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.manager-header h3 {
  color: #4ecdc4;
  margin: 0;
  font-size: 1.5rem;
}

.close-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 2rem;
  cursor: pointer;
  padding: 0 10px;
  line-height: 1;
}

.close-btn:hover {
  color: #ff6b6b;
}

.manager-content {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.section h4 {
  color: #4ecdc4;
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
}

.search-box, .manual-add {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.search-box input, .manual-add input {
  flex: 1;
  padding: 0.8rem;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 8px;
  color: #fff;
  font-size: 1rem;
}

.search-box button, .manual-add button, .bulk-actions button {
  padding: 0.8rem 1.5rem;
  background: #4ecdc4;
  border: none;
  border-radius: 8px;
  color: #1a1a2e;
  font-weight: bold;
  font-size: 1rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.search-box button:hover, .manual-add button:hover, .bulk-actions button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(78, 205, 196, 0.3);
}

.search-box button:disabled, .manual-add button:disabled, .bulk-actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.search-hint {
  font-size: 0.9rem;
  color: #ffaa00;
  margin-bottom: 1rem;
  padding: 0.5rem;
  background: rgba(255, 170, 0, 0.1);
  border-radius: 4px;
}

.search-results {
  max-height: 350px;
  overflow-y: auto;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  margin-top: 1rem;
}

.results-header {
  padding: 0.8rem 1rem;
  background: rgba(78, 205, 196, 0.2);
  color: #4ecdc4;
  font-weight: bold;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.result-item:hover {
  background: rgba(255,255,255,0.05);
}

.result-item:last-child {
  border-bottom: none;
}

.symbol {
  font-weight: bold;
  color: #fff;
  font-size: 1.1rem;
}

.add-btn {
  padding: 0.4rem 1rem;
  border-radius: 20px;
  border: none;
  background: #4ecdc4;
  color: #1a1a2e;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
}

.add-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.add-btn:disabled {
  background: #2a5a55;
  color: #fff;
  cursor: default;
}

.results-footer {
  padding: 1rem;
  text-align: center;
  border-top: 1px solid rgba(255,255,255,0.1);
}

.more-btn {
  padding: 0.6rem 1.2rem;
  background: rgba(78, 205, 196, 0.2);
  border: 1px solid #4ecdc4;
  border-radius: 20px;
  color: #4ecdc4;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
}

.more-btn:hover {
  background: #4ecdc4;
  color: #1a1a2e;
}

textarea {
  width: 100%;
  padding: 1rem;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 8px;
  color: #fff;
  font-family: monospace;
  font-size: 1rem;
  margin-bottom: 1rem;
  resize: vertical;
}

.bulk-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.ticker-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
}

.ticker-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.ticker-item:hover {
  background: rgba(255,255,255,0.05);
}

.ticker-item:last-child {
  border-bottom: none;
}

.ticker-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 40px;
  height: 40px;
  border-radius: 20px;
  border: none;
  background: rgba(78, 205, 196, 0.2);
  color: #4ecdc4;
  cursor: pointer;
  font-size: 1.2rem;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #4ecdc4;
  color: #1a1a2e;
  transform: scale(1.1);
}

.action-btn.delete:hover {
  background: #ff6b6b;
  color: #fff;
}

.status-bar {
  padding: 1rem 1.5rem;
  margin: 0 1.5rem 1.5rem 1.5rem;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1rem;
}

.status-bar.info {
  background: rgba(78, 205, 196, 0.2);
  border: 1px solid #4ecdc4;
}

.status-bar.success {
  background: rgba(76, 175, 80, 0.2);
  border: 1px solid #4caf50;
}

.status-bar.error {
  background: rgba(255, 107, 107, 0.2);
  border: 1px solid #ff6b6b;
}

.status-close {
  background: none;
  border: none;
  color: #fff;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0 5px;
}
</style>