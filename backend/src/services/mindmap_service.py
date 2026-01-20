from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


RawPoint = Union[str, Dict[str, Any]]


@dataclass
class _Node:
    id: str
    label: str
    children: List["_Node"] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "children": [c.to_dict() for c in self.children],
            "meta": self.meta,
        }


class MindmapService:
    """
    Build mindmap trees from slide title + raw_points (with optional levels).

    Output:
      { "root": { id, label, children: [...] } }
    """

    def build_mindmap(
        self,
        title: str,
        raw_points: Optional[List[RawPoint]] = None,
        *,
        max_depth: int = 4,
        max_children_per_node: int = 20,
    ) -> Dict[str, Any]:
        title = (title or "").strip() or "Mindmap"
        raw_points = raw_points or []

        root = _Node(id="root", label=title, meta={"kind": "root"})

        stack: List[_Node] = [root]            # latest node per level
        current_levels: List[int] = [-1]       # root is level -1

        def _normalize_point(p: RawPoint) -> Optional[Dict[str, Any]]:
            if p is None:
                return None
            if isinstance(p, str):
                txt = p.strip()
                if not txt:
                    return None
                return {"level": 0, "text": txt}
            if isinstance(p, dict):
                txt = str(p.get("text", "")).strip()
                if not txt:
                    return None
                level = p.get("level", 0)
                try:
                    level = int(level)
                except Exception:
                    level = 0
                level = max(0, level)
                return {"level": level, "text": txt}
            return None

        node_counter = 0
        for p in raw_points:
            item = _normalize_point(p)
            if not item:
                continue

            level = min(item["level"], max_depth - 1)
            label = item["text"]

            # ensure stack depth = level + 2 (root + levels)
            while current_levels and current_levels[-1] >= level:
                stack.pop()
                current_levels.pop()

            parent = stack[-1] if stack else root
            if len(parent.children) >= max_children_per_node:
                continue

            node_counter += 1
            node = _Node(id=f"n{node_counter}", label=label, meta={"kind": "point", "level": level})
            parent.children.append(node)

            stack.append(node)
            current_levels.append(level)

        return {"root": root.to_dict()}

    def build_mindmap_for_ppt(
        self,
        slides: List[Dict[str, Any]],
        deck_title: str = "PPT Mindmap",
        *,
        max_depth: int = 4,
        max_children_per_node: int = 20,
    ) -> Dict[str, Any]:
        """
        Build a mindmap for the whole PPT:
          root -> section(group) -> slide -> bullet/point (respecting levels where provided).

        "section" is inferred from slide["type"] == "section"/"cover"/"toc" where available.
        """
        deck_title = (deck_title or "").strip() or "PPT Mindmap"
        root = _Node(id="root", label=deck_title, meta={"kind": "deck"})

        node_counter = 0
        section_counter = 0
        current_section: Optional[_Node] = None

        def _ensure_section(title: str) -> _Node:
            nonlocal section_counter, current_section
            if current_section and current_section.label == title:
                return current_section
            section_counter += 1
            current_section = _Node(
                id=f"sec{section_counter}",
                label=title,
                meta={"kind": "section"},
            )
            root.children.append(current_section)
            return current_section

        # default section
        _ensure_section("未分组")

        for slide in slides:
            slide_type = str(slide.get("type") or "").strip().lower()
            slide_title = str(slide.get("title") or f"Slide {slide.get('page_num', '')}").strip()
            page_num = slide.get("page_num")

            # infer section boundaries
            if slide_type in {"section"}:
                _ensure_section(slide_title or "章节")
                continue
            if slide_type in {"cover"}:
                # use cover as deck title hint (but keep current section)
                if slide_title:
                    root.label = slide_title
                # keep default section
                continue
            if slide_type in {"toc"}:
                _ensure_section("目录")

            node_counter += 1
            slide_node = _Node(
                id=f"s{node_counter}",
                label=slide_title or f"Slide {page_num or node_counter}",
                meta={
                    "kind": "slide",
                    "page_num": page_num,
                    "type": slide.get("type"),
                    "images": slide.get("images") or [],
                    "references": slide.get("references") or [],
                },
            )
            (current_section or root).children.append(slide_node)

            # reuse build_mindmap logic for points, but attach under slide_node
            sub_tree = self.build_mindmap(
                title=slide_title,
                raw_points=slide.get("raw_points") or [],
                max_depth=max_depth,
                max_children_per_node=max_children_per_node,
            )["root"]

            # attach sub_tree children under slide_node (skip duplicated root label)
            for child in sub_tree.get("children", []):
                slide_node.children.append(self._dict_to_node(child))

        return {"root": root.to_dict()}

    def _dict_to_node(self, data: Dict[str, Any]) -> _Node:
        children = [self._dict_to_node(c) for c in data.get("children", [])]
        return _Node(
            id=str(data.get("id", "")),
            label=str(data.get("label", "")),
            children=children,
            meta=data.get("meta") or {},
        )


