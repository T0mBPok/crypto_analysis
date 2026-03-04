// src/composables/useCytoscape.js
import { ref } from 'vue'
import cytoscape from 'cytoscape'

export function useCytoscape() {
  const cy = ref(null)

  const initCy = ({ onNodeClick, onEdgeClick, onBackgroundClick }) => {
    cy.value = cytoscape({
      container: document.getElementById('cy'),
      style: [
        { 
          selector: 'node', 
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'color': '#ffffff',
            'text-valign': 'center',
            'text-halign': 'center',
            'width': 45,
            'height': 45,
            'font-size': 14,
            'font-weight': 'bold',
            'border-width': 3,
            'border-color': '#ffffff',
            'border-opacity': 0.8,
            'text-outline-width': 2,
            'text-outline-color': '#000000',
            'text-outline-opacity': 0.8,
            'text-shadow': '2px 2px 4px rgba(0,0,0,0.9)',
            'z-index': 10
          }
        },
        { 
          selector: 'edge', 
          style: {
            'width': 'data(width)',
            'line-color': 'data(color)',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': 12,
            'font-weight': 'bold',
            'color': '#ffffff',
            'text-background-color': '#000000',
            'text-background-opacity': 0.9,
            'text-background-shape': 'roundrectangle',
            'text-background-padding': '5px',
            'text-border-width': 1,
            'text-border-color': 'data(color)',
            'text-border-opacity': 1,
            'text-margin-y': -15,
            'text-shadow': '1px 1px 2px rgba(0,0,0,0.8)',
            'z-index': 5
          }
        },
        { 
          selector: 'node:selected', 
          style: { 
            'border-width': 5, 
            'border-color': '#ffff00', 
            'border-opacity': 1,
            'background-opacity': 1,
            'text-outline-width': 3,
            'text-outline-color': '#000000',
            'z-index': 9999 
          }
        },
        { 
          selector: 'edge:selected', 
          style: { 
            'width': 10, 
            'line-opacity': 1,
            'text-background-opacity': 1,
            'text-background-color': '#000000',
            'z-index': 9999 
          }
        }
      ],
      layout: { 
        name: 'cose',
        idealEdgeLength: 150,
        nodeOverlap: 20,
        refresh: 20,
        fit: true,
        padding: 50,
        randomize: false,
        componentSpacing: 200,
        nodeRepulsion: 800000,
        nodeGravity: 10,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 5,
        numIter: 2000,
        initialTemp: 1000,
        coolingFactor: 0.95,
        minTemp: 1.0,
        animate: true,
        animationDuration: 1500
      },
      wheelSensitivity: 0.4
    })

    cy.value.on('click', 'node', (evt) => onNodeClick?.(evt.target))
    cy.value.on('click', 'edge', (evt) => onEdgeClick?.(evt.target))
    cy.value.on('click', (evt) => {
      if (evt.target === cy.value) onBackgroundClick?.()
    })
    
    cy.value.on('mouseover', 'node', (evt) => {
      evt.target.style('background-opacity', 0.9)
      evt.target.style('border-width', 4)
      document.body.style.cursor = 'pointer'
    })
    
    cy.value.on('mouseout', 'node', (evt) => {
      evt.target.style('background-opacity', 1)
      evt.target.style('border-width', 3)
      document.body.style.cursor = 'default'
    })

    cy.value.on('mouseover', 'edge', (evt) => {
      evt.target.style('width', evt.target.data('width') + 2)
      evt.target.style('text-background-opacity', 1)
      document.body.style.cursor = 'pointer'
    })

    cy.value.on('mouseout', 'edge', (evt) => {
      evt.target.style('width', evt.target.data('width'))
      evt.target.style('text-background-opacity', 0.9)
      document.body.style.cursor = 'default'
    })
  }

  const relayout = () => {
    if (!cy.value) return
    
    cy.value.layout({
      name: 'cose',
      idealEdgeLength: 150,
      nodeOverlap: 20,
      refresh: 20,
      fit: true,
      padding: 50,
      randomize: true,
      componentSpacing: 200,
      nodeRepulsion: 800000,
      nodeGravity: 10,
      edgeElasticity: 100,
      nestingFactor: 5,
      gravity: 5,
      numIter: 2000,
      initialTemp: 1000,
      coolingFactor: 0.95,
      minTemp: 1.0,
      animate: true,
      animationDuration: 1500
    }).run()
  }

  const layoutCircle = () => {
    if (!cy.value) return
    
    cy.value.layout({
      name: 'circle',
      fit: true,
      padding: 50,
      animate: true,
      animationDuration: 1000,
      radius: 400,
      startAngle: 0
    }).run()
  }

  const layoutGrid = () => {
    if (!cy.value) return
    
    cy.value.layout({
      name: 'grid',
      fit: true,
      padding: 50,
      animate: true,
      animationDuration: 1000,
      rows: undefined,
      cols: undefined
    }).run()
  }

  const zoom = (factor) => {
    if (!cy.value) return
    
    if (factor === 1) {
      cy.value.fit(undefined, 50)
    } else {
      const z = cy.value.zoom() * factor
      cy.value.zoom({ level: Math.max(0.1, Math.min(3, z)) })
    }
  }

  return {
    cy,
    initCy,
    relayout,
    layoutCircle,
    layoutGrid,
    zoom
  }
}