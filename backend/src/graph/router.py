from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from src.correlation.logic import CorrelationLogic
from src.correlation.model import Correlation
from src.database import get_neo4j_session

router = APIRouter(prefix="/graph", tags=["Graph Visualization"])

@router.get("/full")
async def get_full_graph(
    limit: int = Query(200000, ge=1, le=2000),
    threshold: float = Query(0.0, ge=0, le=1),
    strength: Optional[str] = Query(None, pattern="^(STRONG|MODERATE|WEAK)?$")
):
    correlations: list[Correlation] = await CorrelationLogic.get_all_correlations(
        limit=limit,
        threshold=threshold,
        strength_filter=strength
    )
    
    # Строим граф
    nodes = {}
    edges = []
    
    for corr in correlations:
        src, tgt = corr.symbol1, corr.symbol2
        
        # Ноды
        nodes[src] = {
            "id": src, 
            "label": src, 
            "type": "Ticker", 
            "color": "#4ecdc4"
        }
        nodes[tgt] = {
            "id": tgt, 
            "label": tgt, 
            "type": "Ticker", 
            "color": "#4ecdc4"
        }
        
        # Полные ребра
        edges.append({
            "source": src,
            "target": tgt,
            "label": f"{corr.pearson:.2f}",
            "width": abs(corr.pearson) * 5 + 2,
            "pearson": corr.pearson,
            "spearman": corr.spearman,
            "returns_corr": corr.returns_corr,
            "strength": corr.strength,
            "data_points": corr.data_points,
            "color": "#00ff88" if corr.pearson > 0 else "#ff6b6b"
        })
    
    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "stats": {
            "correlations": len(correlations),
            "threshold": threshold,
            "strength": strength
        }
    }

@router.get("/ticker/{symbol}")
async def get_ticker_graph(symbol: str):
    async with get_neo4j_session() as session:
        # 🎯 3 ОТДЕЛЬНЫХ запроса = НИКАКИХ агрегаций!
        
        # 1. Центр
        center_query = "MATCH (t:Ticker {symbol: $symbol}) RETURN t.symbol, t LIMIT 1"
        center_result = await session.run(center_query, symbol=symbol)
        center_rec = await center_result.single()
        
        if not center_rec:
            return {
                "nodes": [{"id": symbol, "label": symbol + " ⭐", "color": "#ff6b6b"}],
                "edges": []
            }
        
        # 2. Соседи
        neighbors_query = """
        MATCH (center:Ticker {symbol: $symbol})-[]-(neighbor:Ticker)
        WHERE neighbor.symbol IS NOT NULL AND neighbor.symbol <> $symbol
        RETURN DISTINCT neighbor.symbol, neighbor
        LIMIT 10
        """
        neighbors_result = await session.run(neighbors_query, symbol=symbol)
        neighbors_data = await neighbors_result.data()
        
        # 3. Ребра
        edges_query = """
        MATCH (center:Ticker {symbol: $symbol})-[r]-(neighbor:Ticker)
        WHERE neighbor.symbol <> $symbol
        RETURN startNode(r).symbol AS source, 
               endNode(r).symbol AS target, 
               type(r) AS type,
               coalesce(r.pearson, 0) AS pearson
        LIMIT 20
        """
        edges_result = await session.run(edges_query, symbol=symbol)
        edges_data = await edges_result.data()
        
        # ✅ Формируем чистый ответ
        nodes = [{
            "id": center_rec['t.symbol'],
            "label": center_rec['t.symbol'] + " ⭐",
            "type": "Ticker", 
            "color": "#ff6b6b"
        }]
        
        for neigh in neighbors_data:
            nodes.append({
                "id": neigh['neighbor.symbol'],
                "label": neigh['neighbor.symbol'],
                "type": "Ticker",
                "color": "#4ecdc4"
            })
        
        edges = []
        for edge in edges_data:
            edges.append({
                "source": edge['source'],
                "target": edge['target'],
                "label": f"{edge['type']}\n{edge['pearson']:.2f}",
                "width": abs(edge['pearson']) * 4 + 2,
                "color": "#00ff88" if edge['pearson'] > 0 else "#ff6b6b"
            })
        
        return {"nodes": nodes, "edges": edges}