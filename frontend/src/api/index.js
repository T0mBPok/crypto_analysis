// src/api/index.js
import axios from 'axios'

const API_BASE = 'http://localhost:9000'

const api = {
  async request(url) {
    try {
      console.log(`🌐 Запрос: ${url}`)
      const res = await axios.get(`${API_BASE}${url}`, { timeout: 15000 })
      return res.data
    } catch(e) {
      console.error(`❌ Ошибка API ${url}:`, e)
      throw new Error(`API ${url}: ${e.response?.data?.detail || e.message}`)
    }
  },

  async postRequest(url, data = {}) {
    try {
      console.log(`🌐 POST Запрос: ${url}`, data)
      const res = await axios.post(`${API_BASE}${url}`, data, { timeout: 30000 })
      return res.data
    } catch(e) {
      console.error(`❌ Ошибка API ${url}:`, e)
      throw new Error(`API ${url}: ${e.response?.data?.detail || e.message}`)
    }
  },

  // 🔥 Тикеры
  getAllTickers() {
    return this.request('/tickers/')
  },

  searchBybitTickers(category, symbol) {
    return this.request(`/tickers/bybit/?category=${category}${symbol ? `&symbol=${symbol}` : ''}`)
  },

  addTickersBatch(symbols, category = 'spot') {
    return this.postRequest(`/tickers/tickers/batch?category=${category}`, symbols)
  },

  deleteTicker(symbol) {
    return axios.delete(`${API_BASE}/tickers/${symbol}/`)
  },

  // 🔥 Свечи
  pullCandlesForTicker(category, symbol, days = 4, timeframe = 60) {
    return this.postRequest(`/candles/${symbol}/batch/?category=${category}&days=${days}&timeframe=${timeframe}`)
  },

  pullAllCandles(category = 'spot', timeframe = 60, days = 4, max_tickers = 50) {
    return this.postRequest(`/candles/batch/all?category=${category}&timeframe=${timeframe}&days=${days}&max_tickers=${max_tickers}`)
  },

  getCandles(symbol, limit = 100, timeframe = 60) {
    return this.request(`/candles/${symbol}/?limit=${limit}&timeframe=${timeframe}`)
  },

  // 🔥 Корреляции
  getAllCorrelations(limit = null, threshold = 0, strength = null, sort_by = 'pearson') {
    let url = `/correlations/all?threshold=${threshold}&sort_by=${sort_by}`
    if (limit) url += `&limit=${limit}`
    if (strength) url += `&strength=${strength}`
    return this.request(url)
  },

  getCorrelations(symbol, threshold = 0) {
    return this.request(`/correlations/${symbol}?threshold=${threshold}`)
  },

  calculateCorrelation(symbol1, symbol2, category = 'spot', timeframe = 60, days = 30) {
    return this.postRequest(
      `/correlations/calculate?symbol1=${symbol1}&symbol2=${symbol2}&category=${category}&timeframe=${timeframe}&days=${days}`
    )
  },

  calculateBatchCorrelations(symbols, timeframe = 60, days = 30) {
    return this.postRequest(
      `/correlations/batch?timeframe=${timeframe}&days=${days}`,
      symbols
    )
  },

  calculateAllCorrelations(category = 'spot',   timeframe = 60, days = 30, max_tickers = 50) {
    return this.postRequest(
      `/correlations/all-tickers?category=${category}&timeframe=${timeframe}&days=${days}&max_tickers=${max_tickers}`
    )
  },

  // Граф
  getGraph(symbol) {
    return this.request(`/graph/ticker/${symbol}`)
  },

  getFullGraph(limit = 2000) {
    return this.request(`/graph/full?limit=${limit}`)
  },

  getDebug() {
    return this.request('/graph/debug')
  },

  testConnection() {
    return this.request('/')
  }
}

export default api