# 六爻解读多 Agent 系统

基于多 Agent 协作的六爻解读系统，通过三个不同流派的 subagent 分别解读卦象，经过多轮辩论与交叉验证，最终给出综合性的解读结论。

## 功能特点

- **流派多样性**：融合传统正宗派、象数派、盲派三种不同的解读体系
- **对抗性辩论**：通过 10 轮迭代辩论，相互质疑与验证
- **智能收敛**：3条收敛规则（置信度稳定性、高置信度共识、压倒性证据）
- **文献搜索**：基于关键词索引，每个流派可搜索本流派的经典文献典籍
- **持久化存储**：SQLite/PostgreSQL 支持，保存辩论历史和解读报告
- **多模型支持**：支持 Kimi、GLM、DeepSeek、OpenAI、Anthropic、Google Gemini
- **代理支持**：为国际 LLM 提供商提供 HTTP/HTTPS 代理配置
- **交互式界面**：友好的菜单导航，支持文件和文本输入，历史记录管理
- **模块化架构**：
  - Agent 工厂模式，动态创建流派 Agent
  - LLM 适配器模式，统一提供商接口
  - 核心解码器分离，业务逻辑清晰
  - CLI 模块化，易于扩展和维护

## 快速开始

### 1. 创建虚拟环境

```bash
cd /path/to/liuyao_decoder
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或者在 Windows 上: venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填写 API 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 国内提供商（推荐，无需代理）
KIMI_API_KEY=your-kimi-api-key-here
GLM_API_KEY=your-glm-api-key-here
DEEPSEEK_API_KEY=your-deepseek-api-key-here

# 国际提供商（需要代理）
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# 代理配置（可选，用于国际提供商）
HTTP_PROXY=http://127.0.0.1:7891
HTTPS_PROXY=http://127.0.0.1:7891
```

**国内用户推荐**：Kimi > GLM > DeepSeek（均无需代理，速度快）

### 4. 测试配置

```bash
python main.py test-config
```

### 5. 解读卦象

#### 方式一：交互式界面（推荐）

```bash
python main.py interactive
```

交互式界面提供友好的菜单导航：
- 📖 **解读卦象**：支持文件输入或直接粘贴文本
  - 输入方式：选择 `file`（文件）或 `text`（文本）
  - 文本输入：粘贴卦象内容后，在新行输入 `===` 结束
  - 支持直接输入文件路径自动读取
- 📜 **查看历史记录**：表格展示，可查看详情和导出
- 🗑️ **删除记录**：带确认提示
- ⚙️ **测试配置**：检查 API 状态

**文本输入示例**：
```
[0]> 灵光象吉·六爻排盘
... 时间：2025年11月18日 23:57:20
... 占问：事业发展
... 本卦：火天大有
... 变卦：风水涣
... （更多内容...）
... ===
✅ 已读取 10 行文本
```

#### 方式二：命令行模式

```bash
# 从文件解读
python main.py decode examples/sample_hexagram.txt -o report.md

# 直接在命令行传递文本（适用于短文本）
python main.py decode-text "灵光象吉·六爻排盘\n时间：2025年11月18日 23:57:20"

# 查看历史记录
python main.py list

# 查看特定记录
python main.py view <debate_id>

# 删除记录
python main.py delete <debate_id>
```

## 项目结构

```
liuyao_decoder/
├── agents/                     # Agent 模块
│   ├── base_agent.py          # Agent 基类（含文献搜索）
│   ├── agent_factory.py       # Agent 工厂（动态创建流派 Agent）
│   └── orchestrator.py        # 辩论编排器
├── cli/                       # CLI 交互界面
│   ├── commands.py            # 命令处理
│   └── ui.py                  # 用户界面组件
├── core/                      # 核心逻辑
│   └── decoder.py             # 卦象解码器
├── llm/                       # LLM 抽象层
│   ├── base.py                # 抽象基类
│   ├── factory.py             # 客户端工厂
│   ├── http_client.py         # HTTP 客户端（支持代理）
│   ├── provider_config.py     # 提供商配置
│   └── providers/             # LLM 提供商适配器
│       ├── __init__.py
│       ├── base_adapter.py    # 适配器基类
│       ├── kimi_adapter.py    # Kimi 适配器
│       ├── glm_adapter.py     # GLM 适配器
│       ├── deepseek_adapter.py # DeepSeek 适配器
│       ├── openai_adapter.py  # OpenAI 适配器
│       ├── anthropic_adapter.py # Anthropic 适配器
│       └── gemini_adapter.py  # Gemini 适配器
├── utils/                     # 工具模块
│   ├── parser.py              # 卦象解析器
│   ├── report_generator.py    # 报告生成器
│   ├── literature_search.py   # 文献搜索
│   ├── convergence_detector.py # 收敛检测
│   └── text_utils.py          # 文本处理工具
├── storage/                   # 存储模块
│   ├── models.py              # 数据模型（Pydantic + SQLAlchemy ORM）
│   ├── database.py            # 数据库管理器
│   └── migrations/            # Alembic 数据库迁移
├── prompts/                   # Prompt 模板
│   ├── traditional.md         # 传统正宗派提示
│   ├── xiangshu.md            # 象数派提示
│   └── mangpai.md             # 盲派提示
├── knowledge_base/            # 文献库
│   ├── traditional/           # 传统正宗派文献
│   ├── xiangshu/              # 象数派文献
│   └── mangpai/               # 盲派文献
├── config/
│   └── config.yaml            # 配置文件
├── tests/                     # 测试
│   ├── test_llm_clients.py    # LLM 客户端测试
│   └── integration/           # 集成测试
├── examples/                  # 示例
│   └── sample_hexagram.txt    # 示例卦象
├── main.py                    # CLI 主入口
├── requirements.txt           # Python 依赖
└── README.md                  # 本文件
```

## 配置说明

### LLM 客户端配置

在 `config/config.yaml` 中配置 LLM 客户端：

```yaml
llm:
  default_client: "kimi"

  clients:
    # 国内推荐
    kimi:
      api_key: ${KIMI_API_KEY}
      model: "kimi-k2-thinking-turbo"  # 最新思维模型
      temperature: 0.7
      max_tokens: 4000

    glm:
      api_key: ${GLM_API_KEY}
      model: "glm-4.7"  # 最新模型
      temperature: 0.7
      max_tokens: 4000

    deepseek:
      api_key: ${DEEPSEEK_API_KEY}
      model: "deepseek-reasoner"  # 推理模型
      temperature: 0.7
      max_tokens: 4000

    # 国际提供商（需要代理）
    openai:
      api_key: ${OPENAI_API_KEY}
      model: "gpt-4o"
      temperature: 0.7
      max_tokens: 4000

    anthropic:
      api_key: ${ANTHROPIC_API_KEY}
      model: "claude-sonnet-4-5-20250929"
      temperature: 0.7
      max_tokens: 4000

    gemini:
      api_key: ${GEMINI_API_KEY}
      model: "gemini-2.0-flash-exp"
      temperature: 0.7
      max_tokens: 4000
```

### Agent 配置

为每个流派 Agent 配置使用的 LLM：

```yaml
agents:
  traditional:
    llm_client: "kimi"
    model: "kimi-k2-thinking-turbo"
    school: "传统正宗派"
    prompt_file: "prompts/traditional.md"

  xiangshu:
    llm_client: "kimi"
    model: "kimi-k2-thinking-turbo"
    school: "象数派"
    prompt_file: "prompts/xiangshu.md"

  mangpai:
    llm_client: "kimi"
    model: "kimi-k2-thinking-turbo"
    school: "盲派"
    prompt_file: "prompts/mangpai.md"
```

### 辩论配置

```yaml
debate:
  max_rounds: 3               # 最大辩论轮数
  convergence_threshold: 0.9  # 收敛阈值
  confidence_stability_threshold: 0.5  # 置信度稳定性阈值
```

### 代理配置

对于国际 LLM 提供商（OpenAI、Anthropic、Gemini），可以在 `.env` 中配置代理：

```env
HTTP_PROXY=http://127.0.0.1:7891
HTTPS_PROXY=http://127.0.0.1:7891
```

系统会自动从环境变量读取代理配置并应用到国际提供商。

### 数据库配置

默认使用 SQLite，自动创建 `liuyao_decoder.db`。要使用 PostgreSQL：

```env
DATABASE_URL=postgresql://user:password@localhost/liuyao_decoder
```

## 实施状态

### ✅ 阶段 1：核心辩论系统（已完成）
- [x] LLM 抽象层（6个提供商：Kimi, GLM, DeepSeek, OpenAI, Anthropic, Gemini）
- [x] 数据模型（Pydantic）
- [x] 配置加载模块
- [x] Agent 基类和三个流派实现
- [x] 辩论编排器（DebateOrchestrator）
  - 10轮辩论管理
  - 并行初始解读
  - 顺序辩论流程
  - 3条收敛规则
- [x] 报告生成器（ReportGenerator）
  - 7章节结构化报告
  - 共识度和置信度分析
- [x] CLI 入口（main.py）
  - decode, decode-text, list, view, delete, test-config 命令

### ✅ 阶段 2：架构重构（已完成）
- [x] LLM 适配器模式重构
  - 从独立客户端文件迁移到适配器架构
  - 统一的 HTTP 客户端支持代理
  - 提供商配置集中管理
- [x] Agent 工厂模式
  - 动态创建流派 Agent
  - 消除冗余代码
- [x] CLI 模块化
  - 独立的命令处理模块（cli/commands.py）
  - 用户界面组件（cli/ui.py）
- [x] 核心解码器模块
  - 分离核心业务逻辑
- [x] 文本工具模块
  - 统一的文本处理工具

### ✅ 阶段 3：数据库持久化（已完成）
- [x] SQLAlchemy ORM 模型
- [x] 数据库管理器（DatabaseManager）
  - CRUD 操作
  - 搜索和查询
  - 事务管理
- [x] Alembic 迁移配置
- [x] SQLite 默认支持
- [x] PostgreSQL 可选支持

### ✅ 阶段 4：文献搜索功能（已完成）
- [x] 知识库目录结构（按流派组织）
- [x] 文献搜索服务（LiteratureSearch）
  - 关键词索引（jieba 分词）
  - 搜索和打分算法
  - 片段提取和格式化
- [x] Agent 集成（自动搜索和引用）
- [x] 占位符文献文件（易于扩展）

## 支持的 LLM 模型

| 提供商 | 模型 | 说明 | 推荐场景 |
|--------|------|------|----------|
| **Kimi** | kimi-k2-thinking-turbo | 最新思维模型 | 国内首选 |
| **GLM** | glm-4.7 | 最新模型 | 国内备选 |
| **DeepSeek** | deepseek-reasoner | 推理模型 | 国内备选 |
| **OpenAI** | gpt-4o | 需要代理 | 国际用户 |
| **Anthropic** | claude-sonnet-4-5-20250929 | 需要代理 | 国际用户 |
| **Gemini** | gemini-2.0-flash-exp | 需要代理 | 国际用户 |

**国内用户推荐顺序**：Kimi > GLM > DeepSeek

## 辩论流程

1. **Round 0 - 初始解读**
   - 3 个 Agent 并行独立解读卦象
   - 每个输出初始结论和置信度（0-10）

2. **Round 1-10 - 对抗辩论**
   - 顺序执行，每个 Agent 依次发言
   - 可以保持或调整自己的观点
   - 回应其他 Agent 的质疑
   - 引用文献支持观点

3. **收敛检测**（每轮后检查）
   - 规则1：置信度稳定性（连续3轮变化 < 0.5）
   - 规则2：高置信度共识（所有 Agent ≥ 8.0）
   - 规则3：压倒性证据（2个 Agent ≥ 9.0 且观点一致）

4. **报告生成**
   - 卦象基本信息
   - 核心结论（共识度分析）
   - 详细分析（用神、动爻、六神世应）
   - 流派视角对比
   - 辩论摘要
   - 综合建议
   - 备注

## 测试

### 测试 LLM 客户端

```bash
python tests/test_llm_clients.py
```

### 运行 pytest

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 查看测试覆盖率
pytest --cov=liuyao_decoder --cov-report=html
```

## 扩展文献库

当前使用占位符文献。要添加实际文献：

1. 将文献文本转换为 `.txt` 格式
2. 按照各流派 README 中的格式规范整理
3. 放入对应的 `knowledge_base/<school>/` 目录
4. 重启应用（自动重建索引）

**支持的经典文献**：
- 传统正宗派：《增删卜易》、《卜筮正宗》
- 象数派：《易经系辞》、《梅花易术》
- 盲派：《盲派口诀》

## CLI 命令参考

```bash
# 交互式界面（推荐）
python main.py interactive

# 测试配置
python main.py test-config

# 从文件解读
python main.py decode <file_path> [-o output_file]

# 直接在命令行传递文本解读（适用于短文本）
python main.py decode-text "卦象文本内容"

# 列出所有历史记录
python main.py list

# 查看特定记录
python main.py view <debate_id>

# 删除记录
python main.py delete <debate_id>

# 查看帮助
python main.py --help
python main.py <command> --help
```

## 技术栈

- **Python 3.10+**
- **LLM**: anthropic, openai, google-generativeai, zhipuai, moonshot
- **CLI**: click, rich
- **数据**: Pydantic, SQLAlchemy, Alembic
- **中文处理**: jieba
- **日志**: loguru
- **测试**: pytest
- **架构模式**: Factory Pattern, Adapter Pattern, Composition over Inheritance

## 开发建议

### 1. 使用国内 LLM 提供商

Kimi、GLM、DeepSeek 均无需代理，速度快且性价比高。

### 2. 配置代理访问国际提供商

如需使用 OpenAI、Anthropic 或 Gemini，在 `.env` 中配置代理：

```env
HTTP_PROXY=http://127.0.0.1:7891
HTTPS_PROXY=http://127.0.0.1:7891
```

### 3. 扩展文献库

将实际经典文献添加到 `knowledge_base/` 各流派目录，系统会自动索引。

### 4. 调整辩论参数

在 `config/config.yaml` 中调整 `debate.max_rounds` 和收敛阈值。

### 5. 添加新的 LLM 提供商

使用适配器模式，轻松添加新的提供商：

1. 在 `llm/providers/` 创建新的适配器类，继承 `BaseLLMAdapter`
2. 实现必需的方法：`chat()`, `embeddings()`（可选）
3. 在 `llm/factory.py` 注册新的提供商
4. 在 `config/config.yaml` 添加配置

### 6. 添加新的六爻流派

使用 Agent 工厂模式，添加新的流派：

1. 在 `prompts/` 创建新的提示模板
2. 在 `config/config.yaml` 添加流派配置
3. 使用 `AgentFactory.create_agent()` 动态创建

## 已知限制

1. **文献搜索**：当前使用占位符文件，需添加实际内容
2. **代理配置**：国际提供商需要手动配置代理
3. **LLM 成本**：3轮辩论消耗较多 tokens，建议监控使用量

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献方向

1. 添加更多经典文献到知识库
2. 优化收敛检测算法
3. 支持更多六爻流派
4. 添加 Web 界面
5. 性能优化和缓存

## 联系方式

如有问题或建议，请提交 [Issue](https://github.com/rayanzhang06/liuyao_decoder/issues)。
