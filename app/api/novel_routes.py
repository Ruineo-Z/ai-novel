from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
from typing import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor

from app.novel_generation.novel_workflow import NovelStartFlow, NovelStreamFlow
from app.schemas.base import NovelStyle
from app.core.logger import get_logger
from llama_index.core.workflow import StartEvent

logger = get_logger(__name__)

router = APIRouter()


class NovelGenerationRequest(BaseModel):
    novel_style: NovelStyle


class StreamChunk(BaseModel):
    type: str  # "world_setting", "protagonist", "chapter", "complete"
    data: dict
    message: str = ""


@router.post("/generate-novel-stream")
async def generate_novel_stream(request: NovelGenerationRequest):
    """流式生成小说内容"""
    logger.info(f"开始生成小说，风格: {request.novel_style}")
    
    async def generate():
        try:
            # 创建流式工作流实例
            flow = NovelStreamFlow(request.novel_style)
            
            # 使用真正的流式方法
            async for stream_data in flow.run_with_streaming():
                chunk = StreamChunk(
                    type=stream_data["event_type"],
                    data=stream_data["data"],
                    message=stream_data["message"]
                )
                yield f"data: {json.dumps(chunk.model_dump(), ensure_ascii=False)}\n\n"
                
                # 如果是完成事件，结束流
                if stream_data["event_type"] == "complete":
                    break
            
        except Exception as e:
            logger.error(f"生成小说时出错: {e}")
            error_chunk = StreamChunk(
                type="error",
                data={"error": str(e)},
                message=f"生成失败: {str(e)}"
            )
            yield f"data: {json.dumps(error_chunk.model_dump(), ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@router.post("/generate-novel")
async def generate_novel(request: NovelGenerationRequest):
    """非流式生成小说（保持原有功能）"""
    try:
        flow = NovelStartFlow(novel_style=request.novel_style)

        # 在线程池中执行同步的 kickoff 方法
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, flow.kickoff)

        return {
            "world_setting": flow.state.world_setting.dict() if flow.state.world_setting else None,
            "protagonist_info": flow.state.protagonist_info.dict() if flow.state.protagonist_info else None,
            "start_chapter": flow.state.start_chapter.dict() if flow.state.start_chapter else None,
            "status": "completed" if flow.state.if_finished else "incomplete"
        }
    except Exception as e:
        logger.error(f"生成小说时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
