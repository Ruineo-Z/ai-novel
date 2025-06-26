from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
from typing import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor

from app.novel_generation.novel_workflow import NovelStartFlow
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
            # 创建流程实例
            flow = NovelStartFlow(request.novel_style)
            
            # 生成世界观
            yield f"data: {json.dumps(StreamChunk(type='status', data={}, message='正在生成世界观设定...').model_dump(), ensure_ascii=False)}\n\n"
            
            # 运行workflow
            result = await flow.run()
            
            # 获取生成的内容
            world_setting = flow.state.world_setting
            protagonist = flow.state.protagonist_info
            chapter = flow.state.start_chapter
            
            if world_setting:
                yield f"data: {json.dumps(StreamChunk(type='world_setting', data=world_setting.model_dump(), message='世界观设定完成').model_dump(), ensure_ascii=False)}\n\n"
            
            if protagonist:
                yield f"data: {json.dumps(StreamChunk(type='protagonist', data=protagonist.model_dump(), message='主人公信息完成').model_dump(), ensure_ascii=False)}\n\n"
            
            if chapter:
                yield f"data: {json.dumps(StreamChunk(type='chapter', data=chapter.model_dump(), message='第一章内容完成').model_dump(), ensure_ascii=False)}\n\n"
            
            # 完成
            yield f"data: {json.dumps(StreamChunk(type='complete', data={'finished': True}, message='小说生成完成！').model_dump(), ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"生成小说时出错: {e}")
            yield f"data: {json.dumps(StreamChunk(type='error', data={'error': str(e)}, message=f'生成失败: {str(e)}').model_dump(), ensure_ascii=False)}\n\n"
    
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
