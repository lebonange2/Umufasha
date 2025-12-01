"""API routes for mindmap system."""
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import structlog

from app.database import get_db
from app.models import Mindmap, MindmapNode
from app.schemas import (
    MindmapCreate,
    MindmapUpdate,
    MindmapResponse,
    MindmapListResponse,
    MindmapNodeBase,
    MindmapNodeCreate,
    MindmapNodeUpdate,
    MindmapNodeResponse
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/mindmaps", tags=["mindmaps"])


@router.get("/", response_model=List[MindmapListResponse])
async def list_mindmaps(
    db: AsyncSession = Depends(get_db),
    owner_id: Optional[str] = None
):
    """List all mind maps, optionally filtered by owner."""
    query = select(Mindmap)
    
    if owner_id:
        query = query.where(Mindmap.owner_id == owner_id)
    
    query = query.order_by(Mindmap.updated_at.desc())
    
    result = await db.execute(query)
    mindmaps = result.scalars().all()
    
    # Get node counts
    mindmap_list = []
    for mindmap in mindmaps:
        node_count_result = await db.execute(
            select(func.count(MindmapNode.id)).where(MindmapNode.mindmap_id == mindmap.id)
        )
        node_count = node_count_result.scalar() or 0
        
        mindmap_list.append(MindmapListResponse(
            id=mindmap.id,
            title=mindmap.title,
            owner_id=mindmap.owner_id,
            created_at=mindmap.created_at,
            updated_at=mindmap.updated_at,
            node_count=node_count
        ))
    
    return mindmap_list


@router.get("/{mindmap_id}", response_model=MindmapResponse)
async def get_mindmap(
    mindmap_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a single mind map with all nodes."""
    result = await db.execute(
        select(Mindmap)
        .options(selectinload(Mindmap.nodes))
        .where(Mindmap.id == mindmap_id)
    )
    mindmap = result.scalar_one_or_none()
    
    if not mindmap:
        raise HTTPException(status_code=404, detail="Mind map not found")
    
    return MindmapResponse(
        id=mindmap.id,
        title=mindmap.title,
        owner_id=mindmap.owner_id,
        created_at=mindmap.created_at,
        updated_at=mindmap.updated_at,
        nodes=[
            MindmapNodeResponse(
                id=node.id,
                parent_id=node.parent_id,
                x=node.x,
                y=node.y,
                text=node.text,
                color=node.color,
                text_color=node.text_color,
                shape=node.shape,
                width=node.width,
                height=node.height,
                created_at=node.created_at,
                updated_at=node.updated_at
            )
            for node in mindmap.nodes
        ]
    )


@router.post("/", response_model=MindmapResponse)
async def create_mindmap(
    mindmap_data: MindmapCreate,
    db: AsyncSession = Depends(get_db),
    owner_id: Optional[str] = None
):
    """Create a new mind map."""
    # Create mindmap
    mindmap = Mindmap(
        title=mindmap_data.title,
        owner_id=owner_id
    )
    db.add(mindmap)
    await db.flush()  # Get the ID
    
    # Create nodes if provided
    nodes = []
    if mindmap_data.nodes:
        for node_data in mindmap_data.nodes:
            node = MindmapNode(
                mindmap_id=mindmap.id,
                parent_id=node_data.parent_id,
                x=node_data.x,
                y=node_data.y,
                text=node_data.text,
                color=node_data.color,
                text_color=node_data.text_color,
                shape=node_data.shape
            )
            nodes.append(node)
            db.add(node)
    else:
        # Create a default central node
        central_node = MindmapNode(
            mindmap_id=mindmap.id,
            parent_id=None,
            x=400,
            y=300,
            text="Central Idea",
            color="#4facfe",
            text_color="#ffffff",
            shape="rect"
        )
        nodes.append(central_node)
        db.add(central_node)
    
    await db.commit()
    await db.refresh(mindmap)
    
    # Load nodes
    result = await db.execute(
        select(MindmapNode).where(MindmapNode.mindmap_id == mindmap.id)
    )
    loaded_nodes = result.scalars().all()
    
    return MindmapResponse(
        id=mindmap.id,
        title=mindmap.title,
        owner_id=mindmap.owner_id,
        created_at=mindmap.created_at,
        updated_at=mindmap.updated_at,
        nodes=[
            MindmapNodeResponse(
                id=node.id,
                parent_id=node.parent_id,
                x=node.x,
                y=node.y,
                text=node.text,
                color=node.color,
                text_color=node.text_color,
                shape=node.shape,
                width=node.width,
                height=node.height,
                created_at=node.created_at,
                updated_at=node.updated_at
            )
            for node in loaded_nodes
        ]
    )


@router.put("/{mindmap_id}", response_model=MindmapResponse)
async def update_mindmap(
    mindmap_id: str,
    mindmap_data: MindmapUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a mind map (title and/or nodes)."""
    result = await db.execute(
        select(Mindmap)
        .options(selectinload(Mindmap.nodes))
        .where(Mindmap.id == mindmap_id)
    )
    mindmap = result.scalar_one_or_none()
    
    if not mindmap:
        raise HTTPException(status_code=404, detail="Mind map not found")
    
    # Update title if provided
    if mindmap_data.title is not None:
        mindmap.title = mindmap_data.title
    
    # Update nodes if provided
    if mindmap_data.nodes is not None:
        # Delete existing nodes
        result = await db.execute(
            select(MindmapNode).where(MindmapNode.mindmap_id == mindmap_id)
        )
        existing_nodes = result.scalars().all()
        for node in existing_nodes:
            await db.delete(node)
        
        # Create new nodes
        for node_data in mindmap_data.nodes:
            node = MindmapNode(
                mindmap_id=mindmap.id,
                parent_id=node_data.parent_id,
                x=node_data.x,
                y=node_data.y,
                text=node_data.text,
                color=node_data.color,
                text_color=node_data.text_color,
                shape=node_data.shape,
                width=node_data.width,
                height=node_data.height
            )
            db.add(node)
    
    await db.commit()
    await db.refresh(mindmap)
    
    # Reload nodes
    result = await db.execute(
        select(MindmapNode).where(MindmapNode.mindmap_id == mindmap.id)
    )
    loaded_nodes = result.scalars().all()
    
    return MindmapResponse(
        id=mindmap.id,
        title=mindmap.title,
        owner_id=mindmap.owner_id,
        created_at=mindmap.created_at,
        updated_at=mindmap.updated_at,
        nodes=[
            MindmapNodeResponse(
                id=node.id,
                parent_id=node.parent_id,
                x=node.x,
                y=node.y,
                text=node.text,
                color=node.color,
                text_color=node.text_color,
                shape=node.shape,
                width=node.width,
                height=node.height,
                created_at=node.created_at,
                updated_at=node.updated_at
            )
            for node in loaded_nodes
        ]
    )


@router.delete("/{mindmap_id}")
async def delete_mindmap(
    mindmap_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a mind map and all its nodes."""
    result = await db.execute(
        select(Mindmap).where(Mindmap.id == mindmap_id)
    )
    mindmap = result.scalar_one_or_none()
    
    if not mindmap:
        raise HTTPException(status_code=404, detail="Mind map not found")
    
    await db.delete(mindmap)
    await db.commit()
    
    return {"message": "Mind map deleted successfully", "id": mindmap_id}


@router.post("/{mindmap_id}/nodes", response_model=MindmapNodeResponse)
async def create_node(
    mindmap_id: str,
    node_data: MindmapNodeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new node in a mind map."""
    # Verify mindmap exists
    result = await db.execute(select(Mindmap).where(Mindmap.id == mindmap_id))
    mindmap = result.scalar_one_or_none()
    if not mindmap:
        raise HTTPException(status_code=404, detail="Mind map not found")
    
    # Verify parent exists if specified
    if node_data.parent_id:
        parent_result = await db.execute(
            select(MindmapNode).where(
                MindmapNode.id == node_data.parent_id,
                MindmapNode.mindmap_id == mindmap_id
            )
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Parent node not found")
    
    node = MindmapNode(
        mindmap_id=mindmap_id,
        parent_id=node_data.parent_id,
        x=node_data.x,
        y=node_data.y,
        text=node_data.text,
        color=node_data.color,
        text_color=node_data.text_color,
        shape=node_data.shape
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)
    
    return MindmapNodeResponse(
        id=node.id,
        parent_id=node.parent_id,
        x=node.x,
        y=node.y,
        text=node.text,
        color=node.color,
        text_color=node.text_color,
        shape=node.shape,
        width=node.width,
        height=node.height,
        created_at=node.created_at,
        updated_at=node.updated_at
    )


@router.put("/{mindmap_id}/nodes/{node_id}", response_model=MindmapNodeResponse)
async def update_node(
    mindmap_id: str,
    node_id: str,
    node_data: MindmapNodeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a node in a mind map."""
    result = await db.execute(
        select(MindmapNode).where(
            MindmapNode.id == node_id,
            MindmapNode.mindmap_id == mindmap_id
        )
    )
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Update fields
    if node_data.parent_id is not None:
        node.parent_id = node_data.parent_id
    if node_data.x is not None:
        node.x = node_data.x
    if node_data.y is not None:
        node.y = node_data.y
    if node_data.text is not None:
        node.text = node_data.text
    if node_data.color is not None:
        node.color = node_data.color
    if node_data.text_color is not None:
        node.text_color = node_data.text_color
    if node_data.shape is not None:
        node.shape = node_data.shape
    if node_data.width is not None:
        node.width = node_data.width
    if node_data.height is not None:
        node.height = node_data.height
    
    await db.commit()
    await db.refresh(node)
    
    return MindmapNodeResponse(
        id=node.id,
        parent_id=node.parent_id,
        x=node.x,
        y=node.y,
        text=node.text,
        color=node.color,
        text_color=node.text_color,
        shape=node.shape,
        width=node.width,
        height=node.height,
        created_at=node.created_at,
        updated_at=node.updated_at
    )


@router.delete("/{mindmap_id}/nodes/{node_id}")
async def delete_node(
    mindmap_id: str,
    node_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a node from a mind map and all its children (recursive)."""
    result = await db.execute(
        select(MindmapNode).where(
            MindmapNode.id == node_id,
            MindmapNode.mindmap_id == mindmap_id
        )
    )
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Recursively delete all children
    async def delete_children_recursive(parent_id: str):
        children_result = await db.execute(
            select(MindmapNode).where(
                MindmapNode.parent_id == parent_id,
                MindmapNode.mindmap_id == mindmap_id
            )
        )
        children = children_result.scalars().all()
        for child in children:
            await delete_children_recursive(child.id)
            await db.delete(child)
    
    await delete_children_recursive(node_id)
    await db.delete(node)
    await db.commit()
    
    return {"message": "Node deleted successfully", "id": node_id}

