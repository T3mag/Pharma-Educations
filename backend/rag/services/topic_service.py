"""Сценарии выбора тем для мини-игр."""

from __future__ import annotations

from typing import Optional

from ..api_models import (
    TopicCatalogResponse,
    TopicCatalogsResponse,
    TopicResponse,
    TopicTreeNodeResponse,
    TopicTreeResponse,
    TopicsResponse,
)
from ..common import normalize_search_text
from ..topics import TopicNode, TopicTree
from .runtime import get_topic_tree


def topic_node_to_response(topic_node: TopicNode) -> TopicResponse:
    """Преобразует внутренний узел дерева тем в API-модель."""

    return TopicResponse(
        id=topic_node.id,
        catalog=topic_node.catalog,
        type=topic_node.catalog,
        title=topic_node.title,
        parent_id=topic_node.parent_id,
        level=topic_node.level,
        path=topic_node.path,
        source_page_path=topic_node.source_page_path,
        code=topic_node.code,
        doc_count=topic_node.doc_count,
        has_children=topic_node.has_children,
    )


def topic_node_to_tree_response(
    topic_node: TopicNode,
    topic_tree: TopicTree,
    *,
    parent_id_override: Optional[str] = None,
    level_offset: int = 0,
    path_prefix: Optional[list[str]] = None,
) -> TopicTreeNodeResponse:
    """Преобразует узел дерева тем в nested API-модель со всеми потомками."""

    child_nodes = [
        topic_tree.nodes[child_id]
        for child_id in topic_tree.children_by_parent.get(topic_node.id, [])
        if child_id in topic_tree.nodes
    ]

    effective_path_prefix = path_prefix or []
    effective_path = effective_path_prefix + topic_node.path
    effective_parent_id = parent_id_override if parent_id_override is not None else topic_node.parent_id
    effective_level = topic_node.level + level_offset

    return TopicTreeNodeResponse(
        id=topic_node.id,
        catalog=topic_node.catalog,
        type=topic_node.catalog,
        title=topic_node.title,
        parent_id=effective_parent_id,
        level=effective_level,
        path=effective_path,
        source_page_path=topic_node.source_page_path,
        code=topic_node.code,
        doc_count=topic_node.doc_count,
        has_children=topic_node.has_children,
        children=[
            topic_node_to_tree_response(
                child_node,
                topic_tree,
                level_offset=level_offset,
                path_prefix=effective_path_prefix,
            )
            for child_node in child_nodes
        ],
    )


def get_topic_catalogs() -> TopicCatalogsResponse:
    """Возвращает четыре основных указателя для выбора темы мини-игры."""

    topic_tree = get_topic_tree()
    return TopicCatalogsResponse(
        catalogs=[
            TopicCatalogResponse(
                id=catalog.id,
                title=catalog.title,
                description=catalog.description,
            )
            for catalog in topic_tree.catalogs
        ]
    )


def get_topics(
    catalog: Optional[str],
    parent_id: Optional[str],
    q: Optional[str],
    limit: int,
) -> TopicsResponse:
    """Возвращает темы из иерархического дерева указателей Vidal."""

    topic_tree = get_topic_tree()
    if q:
        normalized_query = normalize_search_text(q)
        topic_nodes = [
            topic_node
            for topic_node in topic_tree.nodes.values()
            if (not catalog or topic_node.catalog == catalog)
            and (
                normalized_query in normalize_search_text(topic_node.title)
                or normalized_query in normalize_search_text(topic_node.code)
                or normalized_query in normalize_search_text(" ".join(topic_node.path))
            )
        ]
        topic_nodes = sorted(
            topic_nodes,
            key=lambda item: (item.catalog, item.path, item.title),
        )
    elif parent_id:
        topic_nodes = [
            topic_tree.nodes[child_id]
            for child_id in topic_tree.children_by_parent.get(parent_id, [])
            if child_id in topic_tree.nodes
        ]
    elif catalog:
        topic_nodes = [
            topic_tree.nodes[child_id]
            for child_id in topic_tree.children_by_parent.get("", [])
            if child_id in topic_tree.nodes and topic_tree.nodes[child_id].catalog == catalog
        ]
    else:
        topic_nodes = [
            topic_tree.nodes[child_id]
            for child_id in topic_tree.children_by_parent.get("", [])
            if child_id in topic_tree.nodes
        ]

    return TopicsResponse(
        topics=[
            topic_node_to_response(topic_node)
            for topic_node in topic_nodes[:limit]
        ]
    )


def get_topics_tree(catalog: Optional[str]) -> TopicTreeResponse:
    """Возвращает полное дерево тем целиком, optionally ограниченное одним каталогом."""

    topic_tree = get_topic_tree()
    selected_catalogs = [
        topic_catalog
        for topic_catalog in topic_tree.catalogs
        if not catalog or topic_catalog.id == catalog
    ]

    return TopicTreeResponse(
        topics=[
            TopicTreeNodeResponse(
                id=topic_catalog.id,
                catalog=topic_catalog.id,
                type="catalog",
                title=topic_catalog.id,
                parent_id="",
                level=0,
                path=[topic_catalog.id],
                source_page_path="",
                code=topic_catalog.id,
                doc_count=sum(
                    topic_tree.nodes[child_id].doc_count
                    for child_id in topic_tree.children_by_parent.get("", [])
                    if child_id in topic_tree.nodes and topic_tree.nodes[child_id].catalog == topic_catalog.id
                ),
                has_children=any(
                    child_id in topic_tree.nodes and topic_tree.nodes[child_id].catalog == topic_catalog.id
                    for child_id in topic_tree.children_by_parent.get("", [])
                ),
                children=[
                    topic_node_to_tree_response(
                        topic_tree.nodes[child_id],
                        topic_tree,
                        parent_id_override=topic_catalog.id,
                        level_offset=1,
                        path_prefix=[topic_catalog.id],
                    )
                    for child_id in topic_tree.children_by_parent.get("", [])
                    if child_id in topic_tree.nodes and topic_tree.nodes[child_id].catalog == topic_catalog.id
                ],
            )
            for topic_catalog in selected_catalogs
        ]
    )
