from typing import Any, Dict, List


class KnowledgeAgent:
    def enrich(self, slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # 预留：调用 LLM / 向量库 / 外部搜索
        enriched = []
        for s in slides:
            enriched.append({
                **s,
                "expanded_html": "<p>后续在此补充原理、公式推导、代码示例。</p>",
                "references": [
                    {"title": "Wikipedia", "url": "https://wikipedia.org", "source": "Wikipedia"},
                ],
            })
        return enriched
