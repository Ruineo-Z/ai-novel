"""
图谱功能测试脚本

测试Neo4j图谱构建功能，包括：
- 角色提取
- 关系分析
- 图谱构建
- 数据查询
"""

import asyncio
import json
from app.schemas.base import NovelStyle
from app.graph.graph_workflow import NovelGraphWorkflow
from app.graph.config import get_graph_status, check_neo4j_connection
from app.core.logger import get_logger

logger = get_logger(__name__)


async def test_graph_workflow():
    """测试图谱工作流"""
    
    print("🚀 开始测试图谱功能...")
    
    # 检查图谱模块状态
    print("\n📊 检查图谱模块状态...")
    status = get_graph_status()
    print(f"图谱构建启用: {status['graph_building_enabled']}")
    print(f"Neo4j可用: {status['neo4j_available']}")
    print(f"Neo4j配置: {status['neo4j_config']}")
    
    if not status['neo4j_available']:
        print("⚠️  Neo4j不可用，将跳过图谱构建测试")
        print("请确保Neo4j服务正在运行，并检查配置")
        return
    
    # 创建图谱工作流
    print("\n🔧 创建图谱工作流...")
    workflow = NovelGraphWorkflow(
        novel_style=NovelStyle.XIANXIA,
        enable_graph_building=True
    )
    
    # 运行工作流
    print("\n📖 开始生成小说并构建图谱...")
    
    try:
        async for event in workflow.run_with_graph_building():
            event_type = event.get("event_type", "unknown")
            message = event.get("message", "")
            
            # 打印关键事件
            if event_type in [
                "progress", "world_setting", "protagonist", "chapter",
                "graph_init", "graph_progress", "characters_extracted",
                "characters_enriched", "relationships_analyzed", 
                "graph_built", "graph_complete", "complete"
            ]:
                print(f"📝 {event_type}: {message}")
                
                # 打印详细数据（部分事件）
                if event_type == "characters_extracted":
                    data = event.get("data", {})
                    print(f"   提取角色数量: {data.get('count', 0)}")
                    
                elif event_type == "relationships_analyzed":
                    data = event.get("data", {})
                    print(f"   分析关系数量: {data.get('count', 0)}")
                    network_analysis = data.get("network_analysis", {})
                    if network_analysis:
                        print(f"   关系类型分布: {network_analysis.get('relationship_types', {})}")
                        print(f"   中心角色: {[char['name'] for char in network_analysis.get('central_characters', [])]}")
                
                elif event_type == "graph_built":
                    data = event.get("data", {})
                    analytics = data.get("analytics", {})
                    if analytics:
                        print(f"   图谱统计: {analytics.get('total_characters', 0)}个角色, {analytics.get('total_relationships', 0)}个关系")
                        print(f"   网络密度: {analytics.get('network_density', 0):.3f}")
                
                elif event_type == "graph_complete":
                    data = event.get("data", {})
                    summary = data.get("summary", {})
                    print(f"   最终统计: {summary}")
            
            elif event_type == "error" or event_type == "graph_error":
                print(f"❌ 错误: {message}")
                error_data = event.get("data", {})
                if error_data.get("error"):
                    print(f"   详细错误: {error_data['error']}")
    
    except Exception as e:
        print(f"❌ 工作流执行失败: {e}")
        return
    
    # 测试图谱查询功能
    print("\n🔍 测试图谱查询功能...")
    
    try:
        # 获取图谱分析数据
        analytics = await workflow.get_graph_analytics()
        if "error" not in analytics:
            print("📈 图谱分析数据:")
            print(f"   总角色数: {analytics.get('total_characters', 0)}")
            print(f"   总关系数: {analytics.get('total_relationships', 0)}")
            print(f"   中心角色: {analytics.get('central_characters', [])}")
        else:
            print(f"❌ 获取分析数据失败: {analytics['error']}")
        
        # 查询主角的关系网络（假设主角存在）
        if workflow.enriched_characters:
            protagonist_name = workflow.enriched_characters[0].name
            network = await workflow.get_character_network(protagonist_name)
            
            if "error" not in network:
                print(f"\n🕸️  {protagonist_name}的关系网络:")
                print(f"   连接角色数: {network.get('total_connections', 0)}")
                connected = network.get('connected_characters', [])
                if connected:
                    print(f"   连接角色: {', '.join(connected[:5])}")  # 显示前5个
            else:
                print(f"❌ 查询关系网络失败: {network['error']}")
    
    except Exception as e:
        print(f"❌ 图谱查询测试失败: {e}")
    
    print("\n✅ 图谱功能测试完成!")


async def test_neo4j_connection():
    """测试Neo4j连接"""
    
    print("🔌 测试Neo4j连接...")
    
    try:
        is_connected = check_neo4j_connection()
        if is_connected:
            print("✅ Neo4j连接成功!")
        else:
            print("❌ Neo4j连接失败!")
            print("请检查:")
            print("1. Neo4j服务是否正在运行")
            print("2. 连接配置是否正确")
            print("3. 用户名和密码是否正确")
    
    except Exception as e:
        print(f"❌ 连接测试异常: {e}")


async def main():
    """主测试函数"""
    
    print("🎯 AI小说图谱功能测试")
    print("=" * 50)
    
    # 测试Neo4j连接
    await test_neo4j_connection()
    
    print("\n" + "=" * 50)
    
    # 测试图谱工作流
    await test_graph_workflow()


if __name__ == "__main__":
    asyncio.run(main())
