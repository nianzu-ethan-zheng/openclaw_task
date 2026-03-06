"""
OpenClaw 自动化系统测试脚本

用于验证系统功能和配置
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any
import sys

# 尝试导入主模块
try:
    from openclaw_automation import (
        ConfigLoader,
        AutomationConfig,
        OpenClawAutomation,
        WorkspaceManager,
        AgentConfigItem,
        QueryItem,
    )
    MAIN_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"⚠ 警告: 无法导入主模块: {e}")
    MAIN_MODULE_AVAILABLE = False

# 尝试导入 SDK
try:
    from openclaw_sdk import OpenClawClient
    SDK_AVAILABLE = True
except ImportError:
    print("⚠ 警告: openclaw-sdk 未安装")
    SDK_AVAILABLE = False


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def test(self, name: str):
        """测试装饰器"""
        def decorator(func):
            self.tests.append((name, func))
            return func
        return decorator

    async def run_all(self):
        """运行所有测试"""
        print("=" * 60)
        print("OpenClaw 自动化系统测试")
        print("=" * 60)

        for name, test_func in self.tests:
            print(f"\n▶ 测试: {name}")
            try:
                await test_func()
                print(f"  ✅ 通过")
                self.passed += 1
            except AssertionError as e:
                print(f"  ❌ 失败: {e}")
                self.failed += 1
            except Exception as e:
                print(f"  ❌ 错误: {e}")
                self.failed += 1

        print("\n" + "=" * 60)
        print(f"测试结果: {self.passed} 通过, {self.failed} 失败")
        print("=" * 60)

        return self.failed == 0


# 创建测试运行器实例
runner = TestRunner()


# ============================================================================
# 环境检查测试
# ============================================================================

@runner.test("Python 版本检查")
async def test_python_version():
    """检查 Python 版本"""
    import sys
    version = sys.version_info
    assert version.major == 3 and version.minor >= 11, \
        f"需要 Python 3.11+, 当前: {version.major}.{version.minor}"
    print(f"    Python 版本: {version.major}.{version.minor}.{version.micro}")


@runner.test("依赖包检查")
async def test_dependencies():
    """检查必要的依赖包"""
    required = ["pydantic", "asyncio"]
    missing = []

    for package in required:
        try:
            __import__(package)
            print(f"    ✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"    ✗ {package}")

    assert len(missing) == 0, f"缺少依赖包: {', '.join(missing)}"


@runner.test("OpenClaw SDK 可用性")
async def test_sdk_available():
    """检查 OpenClaw SDK 是否可用"""
    assert SDK_AVAILABLE, "openclaw-sdk 未安装"
    print("    ✓ openclaw-sdk 已安装")


@runner.test("主模块导入")
async def test_main_module():
    """检查主模块是否可导入"""
    assert MAIN_MODULE_AVAILABLE, "无法导入主模块"
    print("    ✓ 主模块可用")


# ============================================================================
# 配置测试
# ============================================================================

@runner.test("配置模型验证")
async def test_config_models():
    """测试配置模型"""
    if not MAIN_MODULE_AVAILABLE:
        print("    ⊘ 跳过（主模块不可用）")
        return

    # 测试基本配置
    config = AutomationConfig(
        agents=[
            AgentConfigItem(
                name="test_agent",
                system_prompt="Test prompt"
            )
        ],
        queries=[
            QueryItem(
                agent_name="test_agent",
                text="Test query"
            )
        ]
    )

    assert len(config.agents) == 1
    assert config.agents[0].name == "test_agent"
    assert len(config.queries) == 1
    print("    ✓ 配置模型验证通过")


@runner.test("配置文件加载")
async def test_config_loading():
    """测试配置文件加载"""
    if not MAIN_MODULE_AVAILABLE:
        print("    ⊘ 跳过（主模块不可用）")
        return

    # 创建临时配置
    test_config = {
        "agents": [
            {"name": "test", "system_prompt": "test"}
        ],
        "queries": [
            {"agent_name": "test", "text": "hello"}
        ]
    }

    # 保存到临时文件
    temp_file = Path("test_config_temp.json")
    temp_file.write_text(json.dumps(test_config), encoding="utf-8")

    try:
        # 加载配置
        config = ConfigLoader.load_from_file(str(temp_file))
        assert len(config.agents) == 1
        assert config.agents[0].name == "test"
        print("    ✓ 配置文件加载成功")
    finally:
        # 清理
        if temp_file.exists():
            temp_file.unlink()


@runner.test("字典配置加载")
async def test_dict_config():
    """测试从字典加载配置"""
    if not MAIN_MODULE_AVAILABLE:
        print("    ⊘ 跳过（主模块不可用）")
        return

    config_dict = {
        "agents": [
            {"name": "dict_agent", "system_prompt": "test"}
        ],
        "queries": [
            {"agent_name": "dict_agent", "text": "test"}
        ]
    }

    config = ConfigLoader.load_from_dict(config_dict)
    assert config.agents[0].name == "dict_agent"
    print("    ✓ 字典配置加载成功")


# ============================================================================
# 工作空间测试
# ============================================================================

@runner.test("工作空间创建")
async def test_workspace_creation():
    """测试工作空间创建"""
    if not MAIN_MODULE_AVAILABLE:
        print("    ⊘ 跳过（主模块不可用）")
        return

    test_dir = Path("./test_workspaces")
    workspace_mgr = WorkspaceManager(str(test_dir))

    # 创建工作空间
    workspace = workspace_mgr.get_agent_workspace("test_agent")
    assert workspace.exists()
    assert workspace.is_dir()
    print(f"    ✓ 工作空间已创建: {workspace}")

    # 清理
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)


@runner.test("工作空间文件设置")
async def test_workspace_file_setup():
    """测试工作空间文件设置"""
    if not MAIN_MODULE_AVAILABLE:
        print("    ⊘ 跳过（主模块不可用）")
        return

    import shutil

    # 创建测试目录
    test_dir = Path("./test_workspaces")
    user_dir = Path("./test_user_configs")
    user_dir.mkdir(exist_ok=True)

    # 创建测试文件
    (user_dir / "TEST.md").write_text("Test content", encoding="utf-8")

    try:
        workspace_mgr = WorkspaceManager(str(test_dir))
        workspace_mgr.setup_agent_files(
            agent_name="test_agent",
            config_files=["TEST.md"],
            skill_dirs={},
            user_dir=str(user_dir)
        )

        # 验证文件被复制
        workspace = workspace_mgr.get_agent_workspace("test_agent")
        assert (workspace / "TEST.md").exists()
        print("    ✓ 文件设置成功")

    finally:
        # 清理
        if test_dir.exists():
            shutil.rmtree(test_dir)
        if user_dir.exists():
            shutil.rmtree(user_dir)


# ============================================================================
# 变量替换测试
# ============================================================================

@runner.test("变量替换功能")
async def test_variable_replacement():
    """测试查询文本中的变量替换"""
    if not MAIN_MODULE_AVAILABLE:
        print("    ⊘ 跳过（主模块不可用）")
        return

    from openclaw_automation import QueryOrchestrator
    from openclaw_sdk.core.types import ExecutionResult

    # 创建 mock agent manager
    class MockAgentManager:
        def __init__(self):
            self.agents = {}

    agent_mgr = MockAgentManager()
    orchestrator = QueryOrchestrator(agent_mgr)

    # 设置测试结果
    class MockResult:
        def __init__(self, content):
            self.content = content
            self.success = True

    orchestrator.results["result_agent1"] = MockResult("Test content from agent1")

    # 测试替换
    text = "Process this: {result_agent1}"
    replaced = orchestrator._replace_variables(text)

    assert "Test content from agent1" in replaced
    print("    ✓ 变量替换成功")


# ============================================================================
# OpenClaw 连接测试（可选）
# ============================================================================

@runner.test("OpenClaw 连接测试（可选）")
async def test_openclaw_connection():
    """测试 OpenClaw 连接（需要运行的 OpenClaw 实例）"""
    if not SDK_AVAILABLE:
        print("    ⊘ 跳过（SDK 不可用）")
        return

    try:
        # 尝试连接
        client = OpenClawClient.connect(timeout=5)
        async with client:
            print("    ✓ OpenClaw 连接成功")
            return

    except Exception as e:
        print(f"    ⊘ 跳过（OpenClaw 未运行: {e}）")
        # 这不算失败，因为是可选的
        return


# ============================================================================
# 配置文件验证测试
# ============================================================================

@runner.test("示例配置文件验证")
async def test_example_configs():
    """验证示例配置文件"""
    if not MAIN_MODULE_AVAILABLE:
        print("    ⊘ 跳过（主模块不可用）")
        return

    example_configs = [
        "config_simple.json",
        "config_code_review.json",
        "example_config.json",
    ]

    for config_file in example_configs:
        path = Path(config_file)
        if path.exists():
            try:
                config = ConfigLoader.load_from_file(str(path))
                print(f"    ✓ {config_file} 验证通过")
            except Exception as e:
                raise AssertionError(f"{config_file} 验证失败: {e}")
        else:
            print(f"    ⊘ {config_file} 不存在（跳过）")


# ============================================================================
# 集成测试（需要 OpenClaw）
# ============================================================================

@runner.test("端到端测试（需要 OpenClaw）")
async def test_end_to_end():
    """端到端测试（需要运行的 OpenClaw 实例）"""
    if not MAIN_MODULE_AVAILABLE or not SDK_AVAILABLE:
        print("    ⊘ 跳过（模块不可用）")
        return

    try:
        # 检查 OpenClaw 是否可用
        test_client = OpenClawClient.connect(timeout=3)
        async with test_client:
            pass
    except Exception:
        print("    ⊘ 跳过（OpenClaw 未运行）")
        return

    # 运行简单的端到端测试
    config = AutomationConfig(
        agents=[
            AgentConfigItem(
                name="e2e_test_agent",
                system_prompt="You are a test agent. Always respond with 'Test successful.'"
            )
        ],
        queries=[
            QueryItem(
                agent_name="e2e_test_agent",
                text="Run test",
                timeout=30
            )
        ],
        workspace_base="./test_e2e_workspaces"
    )

    try:
        automation = OpenClawAutomation(config)
        results = await automation.run()

        assert len(results) > 0
        print("    ✓ 端到端测试成功")

    except Exception as e:
        raise AssertionError(f"端到端测试失败: {e}")

    finally:
        # 清理
        import shutil
        test_workspace = Path("./test_e2e_workspaces")
        if test_workspace.exists():
            shutil.rmtree(test_workspace)


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """运行所有测试"""
    success = await runner.run_all()

    if success:
        print("\n🎉 所有测试通过！系统可以正常使用。")
        return 0
    else:
        print("\n⚠ 部分测试失败，请检查上述错误信息。")
        return 1


def run_specific_test(test_name: str):
    """运行特定的测试"""
    for name, test_func in runner.tests:
        if test_name.lower() in name.lower():
            print(f"运行测试: {name}")
            asyncio.run(test_func())
            return

    print(f"未找到测试: {test_name}")
    print("\n可用的测试:")
    for name, _ in runner.tests:
        print(f"  - {name}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 运行特定测试
        run_specific_test(sys.argv[1])
    else:
        # 运行所有测试
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
