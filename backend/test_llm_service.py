#!/usr/bin/env python3
"""
快速诊断脚本 - 测试 LLM 是否正常工作
用法: python test_llm_service.py
"""

import os
import sys
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_section(title):
    """打印分隔符"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_llm_connection():
    """测试 LLM 连接"""
    print_section("第 1 步：测试 LLM 连接")
    
    try:
        from langchain_openai import ChatOpenAI
        print("✅ 成功导入 langchain_openai")
        
        # 检查环境变量
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ 错误：未设置 OPENAI_API_KEY 环境变量")
            print("\n📝 设置方法 (Windows):")
            print("   set OPENAI_API_KEY=sk-...")
            print("\n📝 设置方法 (PowerShell):")
            print("   $env:OPENAI_API_KEY='sk-...'")
            return False
        
        # 只显示前几个字符
        masked_key = api_key[:10] + "..." + api_key[-4:]
        print(f"✅ 已找到 OPENAI_API_KEY: {masked_key}")
        
        # 创建 LLM 实例
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5)
        print("✅ 成功创建 ChatOpenAI 实例")
        
        # 测试简单调用
        print("\n🧪 测试简单 LLM 调用...")
        response = llm.invoke("Say 'Hello'")
        print(f"✅ LLM 响应: {response.content}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("\n💡 解决方案: 安装依赖")
        print("   pip install langchain-openai")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        print(f"\n📝 错误类型: {type(e).__name__}")
        print(f"📝 错误详情: {str(e)}")
        return False

def test_analysis_service():
    """测试页面分析服务"""
    print_section("第 2 步：测试页面分析服务")
    
    try:
        from config import LLMConfig
        from services.page_analysis_service import PageDeepAnalysisService
        
        # 创建 LLM 配置
        print("初始化 LLM 配置...")
        llm_config = LLMConfig()
        print("✅ LLM 配置完成")
        
        # 创建分析服务
        print("创建分析服务...")
        service = PageDeepAnalysisService(llm_config)
        print("✅ 分析服务创建完成")
        
        # 测试数据
        test_data = {
            "page_id": 1,
            "title": "深度学习基础",
            "content": """
            神经网络是深度学习的基础。
            
            主要概念：
            1. 神经元 - 基本计算单元
            2. 权重和偏置 - 可学习的参数
            3. 激活函数 - 非线性转换
            4. 反向传播 - 训练算法
            
            应用领域：
            - 计算机视觉
            - 自然语言处理
            - 语音识别
            """,
            "raw_points": []
        }
        
        # 调用分析
        print(f"\n🧪 测试分析: {test_data['title']}")
        print(f"   内容长度: {len(test_data['content'])} 字符")
        print("\n⏳ 调用 LLM 进行分析（这可能需要几秒钟）...")
        
        result = service.analyze_page(
            page_id=test_data['page_id'],
            title=test_data['title'],
            content=test_data['content'],
            raw_points=test_data['raw_points']
        )
        
        print("\n✅ 分析完成！")
        print(f"\n📊 分析结果:")
        print(f"   - 页面ID: {result.page_id}")
        print(f"   - 标题: {result.title}")
        print(f"   - 深度分析长度: {len(result.deep_analysis)} 字符")
        print(f"   - 关键概念数: {len(result.key_concepts)}")
        print(f"   - 学习目标数: {len(result.learning_objectives)}")
        print(f"   - 参考文献数: {len(result.references)}")
        
        if result.deep_analysis:
            print(f"\n📝 深度分析内容预览:")
            preview = result.deep_analysis[:200] + "..." if len(result.deep_analysis) > 200 else result.deep_analysis
            print(f"   {preview}")
        
        if result.key_concepts:
            print(f"\n🏷️ 关键概念:")
            for i, concept in enumerate(result.key_concepts, 1):
                print(f"   {i}. {concept}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        print(f"\n📝 错误类型: {type(e).__name__}")
        print(f"📝 错误详情: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "🔍 LLM 服务诊断脚本" + " "*28 + "║")
    print("║" + " "*10 + "用于快速排查 LLM 相关问题" + " "*24 + "║")
    print("╚" + "="*58 + "╝")
    
    print("\n📋 诊断清单:")
    print("   1. 测试 LLM 连接")
    print("   2. 测试页面分析服务")
    print("   3. 测试 LLM 调用")
    
    # 测试 1: LLM 连接
    llm_ok = test_llm_connection()
    
    if not llm_ok:
        print_section("诊断结论")
        print("❌ LLM 连接失败")
        print("\n🔧 接下来的步骤:")
        print("   1. 检查 OPENAI_API_KEY 环境变量是否已设置")
        print("   2. 检查 API 密钥是否有效")
        print("   3. 检查网络连接")
        return 1
    
    # 测试 2: 分析服务
    service_ok = test_analysis_service()
    
    if not service_ok:
        print_section("诊断结论")
        print("❌ 分析服务测试失败")
        return 1
    
    # 测试通过
    print_section("诊断结论")
    print("✅ 所有测试通过！")
    print("\n👍 LLM 服务配置正确")
    print("\n后续步骤:")
    print("   1. 启动后端服务: python main.py")
    print("   2. 在前端上传 PPT 文件")
    print("   3. 选择页面进行分析")
    print("   4. 查看分析结果")
    
    return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

