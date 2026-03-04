// src/utils/helpers.js
export default {
  filterDuplicateEdges(edges) {
    const uniqueEdges = []
    const edgeSet = new Set()
    
    edges.forEach(edge => {
      const pair = [edge.source, edge.target].sort().join('-')
      if (!edgeSet.has(pair)) {
        edgeSet.add(pair)
        uniqueEdges.push(edge)
      }
    })
    
    return uniqueEdges
  },

  getCorrelationColor(pearson) {
    const absPearson = Math.abs(pearson || 0)
    if (absPearson > 0.7) return '#00ff88'
    if (absPearson > 0.4) return '#ffaa00'
    return '#ff6b6b'
  },

  getCorrelationWidth(pearson) {
    const absPearson = Math.abs(pearson || 0)
    if (absPearson > 0.7) return 5
    if (absPearson > 0.4) return 3
    return 2
  },

  getStrength(pearson) {
    const absPearson = Math.abs(pearson || 0)
    if (absPearson > 0.7) return 'STRONG'
    if (absPearson > 0.4) return 'MODERATE'
    return 'WEAK'
  },

  formatDate(dateStr) {
    if (!dateStr) return '—'
    const date = new Date(dateStr)
    return date.toLocaleString('ru-RU', { 
      day: '2-digit', 
      month: '2-digit',
      hour: '2-digit', 
      minute: '2-digit' 
    })
  },

  formatCandleTooltip(c) {
    return `${new Date(c.start).toLocaleString()}\nO: ${c.open.toFixed(2)}\nH: ${c.high.toFixed(2)}\nL: ${c.low.toFixed(2)}\nC: ${c.close.toFixed(2)}`
  }
}