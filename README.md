# 六爻解读多 Agent 系统

基于多 Agent 协作的六爻解读系统，通过三个不同流派的 subagent 分别解读卦象，经过多轮辩论与交叉验证，最终给出综合性的解读结论。

## 功能特点

- **流派多样性**：融合传统正宗派、象数派、盲派三种不同的解读体系
- **对抗性辩论**：通过 10 轮迭代辩论，相互质疑与验证
- **收敛机制**：在辩论中寻找共识点，标记分歧点
- **文献搜索**：每个流派可搜索本流派的经典文献典籍
- **持久化存储**：保存辩论历史和解读报告
- **多模型支持**：支持 DeepSeek、Gemini、OpenAI GPT-4、Anthropic Claude 等

## 安装

### 1. 创建虚拟环境

```bash
cd /Users/ruizhang/Desktop/Projects/liuyao_decoder
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
DEEPSEEK_API_KEY=your_deepseek_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key  # 可选
ANTHROPIC_API_KEY=your_anthropic_api_key  # 可选
```

### 4. 准备文献库（可选）

如果需要使用文献搜索功能，将经典文献按流派分类放入 `knowledge_base/` 目录：

```
knowledge_base/
├── traditional/  # 传统正宗派文献
├── xiangshu/     # 象数派文献
└── mangpai/      # 盲派文献
```

## 快速开始

### 激活虚拟环境

```bash
source venv/bin/activate  # macOS/Linux
# 或者在 Windows 上: venv\Scripts\activate
```

### 测试 LLM 客户端

```bash
python tests/test_llm_clients.py
```

**注意**：需要在 `.env` 文件中配置至少一个 LLM API 密钥（DeepSeek、Gemini、OpenAI 或 Anthropic）。

### 运行解读（待实现）

```bash
python main.py
```

## 项目结构

```
liuyao_decoder/
├── agents/                     # Agent 模块
│   ├── base_agent.py          # Agent 基类
│   ├── coordinator.py         # 总控 Agent
│   ├── traditional_agent.py   # 传统正宗派
│   ├── xiangshu_agent.py      # 象数派
│   └── mangpai_agent.py       # 盲派
├── llm/                       # LLM 抽象层
│   ├── base.py               # 抽象基类
│   ├── openai_client.py      # OpenAI 客户端
│   ├── anthropic_client.py   # Anthropic 客户端
│   ├── deepseek_client.py    # DeepSeek 客户端
│   ├── gemini_client.py      # Gemini 客户端
│   └── factory.py            # 客户端工厂
├── utils/                     # 工具模块
│   ├── parser.py             # 卦象解析器
│   ├── debate_manager.py     # 辩论管理器
│   ├── report_generator.py   # 报告生成器
│   ├── literature_search.py  # 文献搜索
│   └── convergence_detector.py # 收敛检测
├── storage/                   # 存储模块
│   ├── storage_service.py    # 存储服务
│   └── models.py             # 数据模型
├── prompts/                   # Prompt 模板
├── knowledge_base/            # 文献库
├── config/                    # 配置文件
│   └── config.yaml
├── tests/                     # 测试
├── main.py                    # 主入口
└── requirements.txt
```

## 配置说明

### LLM 客户端配置

在 `config/config.yaml` 中配置 LLM 客户端（默认使用 Kimi）：

```yaml
llm:
  default_client: "kimi"

  clients:
    kimi:
      api_key: ${KIMI_API_KEY}
      model: "moonshot-v1-8k"
      temperature: 0.7
      max_tokens: 4000

    glm:
      api_key: ${GLM_API_KEY}
      model: "glm-4"
      temperature: 0.7
      max_tokens: 4000

    deepseek:
      api_key: ${DEEPSEEK_API_KEY}
      model: "deepseek-chat"
      temperature: 0.7
      max_tokens: 4000
```

### Agent 配置

为每个流派 Agent 配置使用的 LLM：

```yaml
agents:
  traditional:
    llm_client: "kimi"
    model: "moonshot-v1-8k"
    school: "传统正宗派"
    prompt_file: "prompts/traditional.md"

  xiangshu:
    llm_client: "glm"
    model: "glm-4"
    school: "象数派"
    prompt_file: "prompts/xiangshu.md"

  mangpai:
    llm_client: "kimi"
    model: "moonshot-v1-8k"
    school: "盲派"
    prompt_file: "prompts/mangpai.md"
```

## 开发进度

### 阶段 1：基础架构 ✅
- [x] 项目目录结构
- [x] LLM 抽象层（支持 DeepSeek、Gemini、OpenAI、Anthropic）
- [x] 数据模型
- [x] 配置加载模块

### 阶段 2：Agent 系统（进行中）
- [ ] Agent 基类
- [ ] 三个流派 Agent 实现
- [ ] 卦象输入解析器
- [ ] Prompt 模板

### 阶段 3：核心辩论流程
- [ ] 辩论管理器
- [ ] 状态机逻辑
- [ ] 收敛检测器

### 阶段 4：持久化存储
- [ ] 数据库表设计
- [ ] 存储服务实现

### 阶段 5：文献搜索功能
- [ ] 文献索引
- [ ] 搜索服务实现

### 阶段 6：报告生成
- [ ] 报告模板
- [ ] 报告生成器

### 阶段 7：优化与测试
- [ ] 性能优化
- [ ] 测试完善

## 支持的 LLM 模型

| 提供商 | 模型 | 说明 | 推荐场景 |
|--------|------|------|----------|
| **Kimi** | moonshot-v1-8k | 默认使用，国内访问快 | 推荐，性价比高 |
| **GLM** | glm-4 | 智谱清言，国内访问快 | 备选 |
| DeepSeek | deepseek-chat | 深度求索，国内访问快 | 备选 |
| Google | gemini-pro | 需要代理 | 国际用户 |
| OpenAI | gpt-4-turbo-preview | 需要代理 | 国际用户 |
| Anthropic | claude-3-opus-20240229 | 需要代理 | 国际用户 |

**国内用户推荐使用顺序**：Kimi > GLM > DeepSeek（均无需代理，速度快）

## 测试

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

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请提交 Issue。
