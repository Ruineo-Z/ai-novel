#!/usr/bin/env python3
"""
AI互动小说项目 - 开发进度跟踪脚本
用于统计和显示项目开发进度
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

class ProjectStatusTracker:
    """项目状态跟踪器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.docs_dir = self.project_root / "docs"
        
    def parse_task_checklist(self) -> Dict:
        """解析任务清单文件"""
        checklist_file = self.docs_dir / "task_checklist_phase2.md"
        
        if not checklist_file.exists():
            return {"error": "任务清单文件不存在"}
        
        with open(checklist_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计任务
        total_tasks = len(re.findall(r'- \[ \]', content))
        completed_tasks = len(re.findall(r'- \[x\]', content))
        
        # 解析里程碑
        milestones = self._parse_milestones(content)
        
        # 解析每日任务
        daily_tasks = self._parse_daily_tasks(content)
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0,
            "milestones": milestones,
            "daily_tasks": daily_tasks,
            "last_updated": datetime.now().isoformat()
        }
    
    def _parse_milestones(self, content: str) -> List[Dict]:
        """解析里程碑信息"""
        milestones = []
        
        # 查找里程碑部分
        milestone_pattern = r'### (M\d+): ([^(]+)\(([^)]+)\)'
        matches = re.findall(milestone_pattern, content)
        
        for match in matches:
            milestone_id, name, date = match
            milestones.append({
                "id": milestone_id.strip(),
                "name": name.strip(),
                "date": date.strip(),
                "status": "pending"  # 可以根据任务完成情况动态计算
            })
        
        return milestones
    
    def _parse_daily_tasks(self, content: str) -> Dict:
        """解析每日任务分布"""
        daily_pattern = r'### Day (\d+)(?:-(\d+))?: ([^(]+)\((\d+)/(\d+)项\)'
        matches = re.findall(daily_pattern, content)
        
        daily_tasks = {}
        for match in matches:
            start_day, end_day, task_name, completed, total = match
            
            day_key = f"Day {start_day}" + (f"-{end_day}" if end_day else "")
            daily_tasks[day_key] = {
                "name": task_name.strip(),
                "completed": int(completed),
                "total": int(total),
                "completion_rate": round((int(completed) / int(total) * 100), 1) if int(total) > 0 else 0
            }
        
        return daily_tasks
    
    def get_code_statistics(self) -> Dict:
        """获取代码统计信息"""
        app_dir = self.project_root / "app"
        
        if not app_dir.exists():
            return {"error": "应用目录不存在"}
        
        stats = {
            "python_files": 0,
            "total_lines": 0,
            "code_lines": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "files_by_type": {}
        }
        
        for py_file in app_dir.rglob("*.py"):
            stats["python_files"] += 1
            
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            stats["total_lines"] += len(lines)
            
            for line in lines:
                line = line.strip()
                if not line:
                    stats["blank_lines"] += 1
                elif line.startswith('#'):
                    stats["comment_lines"] += 1
                else:
                    stats["code_lines"] += 1
            
            # 按文件类型分类
            relative_path = py_file.relative_to(app_dir)
            file_type = str(relative_path.parts[0]) if relative_path.parts else "root"
            
            if file_type not in stats["files_by_type"]:
                stats["files_by_type"][file_type] = 0
            stats["files_by_type"][file_type] += 1
        
        return stats
    
    def check_implementation_status(self) -> Dict:
        """检查实现状态"""
        status = {
            "database_models": self._check_models(),
            "crud_operations": self._check_crud(),
            "api_endpoints": self._check_api(),
            "ai_services": self._check_ai_services(),
            "tests": self._check_tests()
        }
        
        return status
    
    def _check_models(self) -> Dict:
        """检查数据模型实现状态"""
        models_dir = self.project_root / "app" / "models"
        expected_models = ["user.py", "story.py", "chapter.py", "choice.py", "memory.py", "progress.py"]
        
        existing = []
        missing = []
        
        for model in expected_models:
            if (models_dir / model).exists():
                existing.append(model)
            else:
                missing.append(model)
        
        return {
            "total": len(expected_models),
            "existing": len(existing),
            "missing": len(missing),
            "existing_files": existing,
            "missing_files": missing,
            "completion_rate": round((len(existing) / len(expected_models) * 100), 1)
        }
    
    def _check_crud(self) -> Dict:
        """检查CRUD操作实现状态"""
        crud_dir = self.project_root / "app" / "crud"
        expected_crud = ["user.py", "story.py", "chapter.py", "choice.py", "memory.py"]
        
        existing = []
        missing = []
        
        for crud in expected_crud:
            if (crud_dir / crud).exists():
                existing.append(crud)
            else:
                missing.append(crud)
        
        return {
            "total": len(expected_crud),
            "existing": len(existing),
            "missing": len(missing),
            "existing_files": existing,
            "missing_files": missing,
            "completion_rate": round((len(existing) / len(expected_crud) * 100), 1)
        }
    
    def _check_api(self) -> Dict:
        """检查API端点实现状态"""
        api_dir = self.project_root / "app" / "api" / "v1"
        expected_api = ["stories.py", "chapters.py", "users.py"]
        
        existing = []
        missing = []
        
        for api in expected_api:
            if (api_dir / api).exists():
                existing.append(api)
            else:
                missing.append(api)
        
        return {
            "total": len(expected_api),
            "existing": len(existing),
            "missing": len(missing),
            "existing_files": existing,
            "missing_files": missing,
            "completion_rate": round((len(existing) / len(expected_api) * 100), 1)
        }
    
    def _check_ai_services(self) -> Dict:
        """检查AI服务实现状态"""
        ai_dir = self.project_root / "app" / "services" / "ai"
        story_dir = self.project_root / "app" / "services" / "story"
        
        expected_ai = ["__init__.py", "base.py", "story_generator.py", "memory_manager.py", "models.py"]
        expected_story = ["__init__.py", "interaction_service.py", "context_manager.py", "generation_service.py"]
        
        ai_existing = [f for f in expected_ai if (ai_dir / f).exists()]
        story_existing = [f for f in expected_story if (story_dir / f).exists()]
        
        total = len(expected_ai) + len(expected_story)
        existing = len(ai_existing) + len(story_existing)
        
        return {
            "total": total,
            "existing": existing,
            "missing": total - existing,
            "ai_services": {
                "existing": ai_existing,
                "missing": [f for f in expected_ai if f not in ai_existing]
            },
            "story_services": {
                "existing": story_existing,
                "missing": [f for f in expected_story if f not in story_existing]
            },
            "completion_rate": round((existing / total * 100), 1)
        }
    
    def _check_tests(self) -> Dict:
        """检查测试实现状态"""
        tests_dir = self.project_root / "tests"
        
        if not tests_dir.exists():
            return {"total": 0, "existing": 0, "completion_rate": 0, "files": []}
        
        test_files = list(tests_dir.glob("test_*.py"))
        
        return {
            "total": len(test_files),
            "existing": len(test_files),
            "completion_rate": 100 if test_files else 0,
            "files": [f.name for f in test_files]
        }
    
    def generate_report(self) -> str:
        """生成项目状态报告"""
        task_status = self.parse_task_checklist()
        code_stats = self.get_code_statistics()
        impl_status = self.check_implementation_status()
        
        report = f"""
# AI互动小说项目开发状态报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 任务完成情况

- **总任务数**: {task_status.get('total_tasks', 0)}
- **已完成**: {task_status.get('completed_tasks', 0)}
- **完成率**: {task_status.get('completion_rate', 0)}%

## 💻 代码统计

- **Python文件数**: {code_stats.get('python_files', 0)}
- **总代码行数**: {code_stats.get('total_lines', 0)}
- **有效代码行**: {code_stats.get('code_lines', 0)}
- **注释行数**: {code_stats.get('comment_lines', 0)}

## 🏗️ 实现状态

### 数据模型
- **完成率**: {impl_status['database_models']['completion_rate']}%
- **已实现**: {', '.join(impl_status['database_models']['existing_files'])}

### CRUD操作
- **完成率**: {impl_status['crud_operations']['completion_rate']}%
- **已实现**: {', '.join(impl_status['crud_operations']['existing_files'])}

### API端点
- **完成率**: {impl_status['api_endpoints']['completion_rate']}%
- **已实现**: {', '.join(impl_status['api_endpoints']['existing_files'])}

### AI服务
- **完成率**: {impl_status['ai_services']['completion_rate']}%
- **AI服务**: {', '.join(impl_status['ai_services']['ai_services']['existing'])}
- **故事服务**: {', '.join(impl_status['ai_services']['story_services']['existing'])}

## 🎯 里程碑状态

"""
        
        for milestone in task_status.get('milestones', []):
            report += f"- **{milestone['id']}**: {milestone['name']} ({milestone['date']})\n"
        
        report += f"""
## 📅 每日任务进度

"""
        
        for day, tasks in task_status.get('daily_tasks', {}).items():
            report += f"- **{day}**: {tasks['name']} - {tasks['completion_rate']}% ({tasks['completed']}/{tasks['total']})\n"
        
        return report
    
    def save_report(self, filename: str = None):
        """保存报告到文件"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"project_status_report_{timestamp}.md"
        
        report = self.generate_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"项目状态报告已保存到: {filename}")
        return filename


def main():
    """主函数"""
    tracker = ProjectStatusTracker()
    
    print("🚀 AI互动小说项目状态检查")
    print("=" * 50)
    
    # 生成并显示报告
    report = tracker.generate_report()
    print(report)
    
    # 保存报告
    filename = tracker.save_report()
    
    print(f"\n📁 详细报告已保存到: {filename}")


if __name__ == "__main__":
    main()
