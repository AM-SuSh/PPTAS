#!/usr/bin/env python3
"""
测试新后端服务的完整性
验证：PageDeepAnalysisService, AITutorService, ReferenceSearchService
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """测试所有导入"""
    print("=" * 60)
    print("📦 测试模块导入...")
    print("=" * 60)
    
    try:
        from services.page_analysis_service import PageDeepAnalysisService, DeepAnalysisResult
        print("✅ PageDeepAnalysisService 导入成功")
    except Exception as e:
        print(f"❌ PageDeepAnalysisService 导入失败: {e}")
        return False
    
    try:
        from services.ai_tutor_service import AITutorService, ChatMessage
        print("✅ AITutorService 导入成功")
    except Exception as e:
        print(f"❌ AITutorService 导入失败: {e}")
        return False
    
    try:
        from services.reference_search_service import ReferenceSearchService, ReferenceItem, ReferenceSearchResult
        print("✅ ReferenceSearchService 导入成功")
    except Exception as e:
        print(f"❌ ReferenceSearchService 导入失败: {e}")
        return False
    
    return True


def test_service_instantiation():
    """测试服务实例化"""
    print("\n" + "=" * 60)
    print("🏗️  测试服务实例化...")
    print("=" * 60)
    
    try:
        from services.ai_tutor_service import AITutorService
        tutor = AITutorService()
        print("✅ AITutorService 实例化成功")
    except Exception as e:
        print(f"❌ AITutorService 实例化失败: {e}")
        return False
    
    try:
        from services.reference_search_service import ReferenceSearchService
        search = ReferenceSearchService()
        print("✅ ReferenceSearchService 实例化成功")
    except Exception as e:
        print(f"❌ ReferenceSearchService 实例化失败: {e}")
        return False
    
    return True


def test_pydantic_models():
    """测试 Pydantic 模型"""
    print("\n" + "=" * 60)
    print("🔧 测试 Pydantic 模型...")
    print("=" * 60)
    
    try:
        from services.page_analysis_service import DeepAnalysisResult
        result = DeepAnalysisResult(
            page_id=1,
            title="测试页面",
            raw_content="测试内容",
            deep_analysis="# AI 深度分析\n深入分析结果",
            key_concepts=["概念1", "概念2"],
            learning_objectives=["目标1", "目标2"],
            references=[
                {"title": "论文1", "url": "http://example.com", "source": "arxiv", "snippet": "摘要"}
            ]
        )
        print("✅ DeepAnalysisResult 模型验证成功")
        print(f"   - Page ID: {result.page_id}")
        print(f"   - 关键概念数: {len(result.key_concepts)}")
        print(f"   - 学习目标数: {len(result.learning_objectives)}")
    except Exception as e:
        print(f"❌ DeepAnalysisResult 模型验证失败: {e}")
        return False
    
    try:
        from services.reference_search_service import ReferenceItem, ReferenceSearchResult
        item = ReferenceItem(
            title="参考文献",
            url="http://example.com",
            source="arxiv",
            snippet="这是摘要"
        )
        result = ReferenceSearchResult(
            query="测试查询",
            total_results=1,
            references=[item]
        )
        print("✅ ReferenceItem & ReferenceSearchResult 模型验证成功")
    except Exception as e:
        print(f"❌ 参考文献模型验证失败: {e}")
        return False
    
    return True


def test_api_endpoints():
    """测试 API 端点定义"""
    print("\n" + "=" * 60)
    print("🔌 检查 API 端点定义...")
    print("=" * 60)
    
    try:
        # 读取 app.py 文件
        with open('src/app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        endpoints = [
            '/api/v1/analyze-page',
            '/api/v1/chat',
            '/api/v1/tutor/set-context',
            '/api/v1/tutor/conversation',
            '/api/v1/search-references',
            '/api/v1/search-by-concepts'
        ]
        
        found_count = 0
        for endpoint in endpoints:
            if endpoint in app_content:
                print(f"✅ 端点 {endpoint} 已定义")
                found_count += 1
            else:
                print(f"⚠️  端点 {endpoint} 未找到")
        
        if found_count == len(endpoints):
            print(f"\n✅ 所有 {len(endpoints)} 个 API 端点已定义")
            return True
        else:
            print(f"\n⚠️  仅找到 {found_count}/{len(endpoints)} 个端点")
            return False
    except Exception as e:
        print(f"❌ 检查 API 端点失败: {e}")
        return False


def test_service_methods():
    """测试服务关键方法"""
    print("\n" + "=" * 60)
    print("⚡ 测试服务核心方法...")
    print("=" * 60)
    
    try:
        from services.ai_tutor_service import AITutorService
        tutor = AITutorService()
        
        # 测试设置页面上下文
        tutor.set_page_context(
            page_id=1,
            title="测试标题",
            content="测试内容",
            concepts=["概念1", "概念2"]
        )
        print("✅ AITutorService.set_page_context() 工作正常")
        
        # 测试获取欢迎消息
        greeting = tutor.get_assistant_greeting(1)
        print(f"✅ AITutorService.get_assistant_greeting() 返回: '{greeting}'")
    except Exception as e:
        print(f"❌ AITutorService 方法测试失败: {e}")
        return False
    
    try:
        from services.reference_search_service import ReferenceSearchService
        search = ReferenceSearchService()
        
        # 验证方法是否存在
        assert hasattr(search, 'search_references'), "search_references 方法不存在"
        assert hasattr(search, 'search_by_concepts'), "search_by_concepts 方法不存在"
        print("✅ ReferenceSearchService 核心方法已实现")
    except Exception as e:
        print(f"❌ ReferenceSearchService 方法验证失败: {e}")
        return False
    
    return True


def test_services_export():
    """测试服务是否正确导出"""
    print("\n" + "=" * 60)
    print("📤 测试服务导出...")
    print("=" * 60)
    
    try:
        from services import PageDeepAnalysisService, AITutorService, ReferenceSearchService
        print("✅ 所有服务从 services 模块正确导出")
        return True
    except Exception as e:
        print(f"❌ 服务导出失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n")
    print("🧪 " + "=" * 56)
    print("     后端新服务完整性验证测试")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("服务实例化", test_service_instantiation),
        ("Pydantic 模型", test_pydantic_models),
        ("API 端点", test_api_endpoints),
        ("服务方法", test_service_methods),
        ("服务导出", test_services_export),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 60)
    print(f"总体结果: {passed}/{total} 个测试通过")
    print("=" * 60)
    
    if passed == total:
        print("\n✨ 所有测试通过！后端新服务已准备就绪。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，需要修复。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
