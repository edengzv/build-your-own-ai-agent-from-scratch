# Bibliography

> 本书参考文献按章节组织。每章列出该章内容涉及的论文、书籍、文档和开源项目。标记 `*` 的条目在该章的 Further Reading 中被直接引用。

---

## 全书通用参考

### 灵感来源

- 斎藤康毅.《深度学习入门2：自制框架》. 人民邮电出版社, 2020. 原书: *ゼロから作る Deep Learning ❸ フレームワーク編*, O'Reilly Japan, 2020. — 本书"从零构建、每章增量演进"的方法论直接借鉴此书的 Step by Step 哲学.
- shareAI-lab. "Learn Claude Code — Harness Engineering for Real Agents." GitHub, 2025. https://github.com/shareAI-lab/learn-claude-code — 本书"Agent = Model + Harness"的核心思想源自此项目的 Harness Engineering 理念.

### API 文档

- Anthropic. "Claude API Documentation." https://docs.anthropic.com/
- OpenAI. "API Reference." https://platform.openai.com/docs/api-reference

---

## Chapter 1: 你好，Agent

- \* Anthropic. "Tool Use Documentation." https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview — 工具调用的官方文档.
- \* Anthropic. "Model Context Protocol (MCP)." https://modelcontextprotocol.io/ — Agent 工具的标准化协议.
- \* Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). "ReAct: Synergizing Reasoning and Acting in Language Models." *ICLR 2023*. https://arxiv.org/abs/2210.03629 — Agent 推理-行动循环的理论基础, 本书 agent_loop 的核心模式.

---

## Chapter 2: 工具调用

- \* JSON Schema. "JSON Schema Specification." https://json-schema.org/ — 工具 schema 的标准规范.
- \* Anthropic. "Tool Use Best Practices." https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview — 工具设计的官方建议.
- \* OWASP. "Path Traversal." https://owasp.org/www-community/attacks/Path_Traversal — 路径遍历攻击的安全参考, safe_path() 的设计依据.

---

## Chapter 3: 对话记忆

- \* Anthropic. "Messages API Reference." https://docs.anthropic.com/en/api/messages — 消息格式的完整规范.
- \* OpenAI. "Chat Completions API." https://platform.openai.com/docs/api-reference/chat — 对比参考: OpenAI 的消息格式.
- \* Park, J.S., O'Brien, J.C., Cai, C.J., Morris, M.R., Liang, P., & Bernstein, M.S. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." *UIST 2023*. https://arxiv.org/abs/2304.03442 — 探讨 Agent 记忆架构的经典论文.

---

## Chapter 4: 任务规划

- \* Yao, S., et al. (2023). "ReAct: Synergizing Reasoning and Acting in Language Models." *ICLR 2023*. — 推理-行动交错模式的理论基础 (同 Ch01).
- \* Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q.V., & Zhou, D. (2022). "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." *NeurIPS 2022*. https://arxiv.org/abs/2201.11903 — 让 LLM 分步思考的经典方法, TodoManager 的"先规划再执行"模式与此相关.
- Huang, W., Abbeel, P., Pathak, D., & Mordatch, I. (2022). "Language Models as Zero-Shot Planners: Extracting Actionable Knowledge for Embodied Agents." *ICML 2022*. https://arxiv.org/abs/2201.07207 — LLM 作为零样本规划器的早期探索.

---

## Chapter 5: 知识加载

- Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Kuttler, H., Lewis, M., Yih, W., Rocktaschel, T., Riedel, S., & Kiela, D. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." *NeurIPS 2020*. https://arxiv.org/abs/2005.11401 — 检索增强生成 (RAG) 的开创性论文, Skill 系统的按需加载思想与 RAG 的"需要时检索"理念一脉相承.
- Anthropic. "System Prompts." https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching — 系统提示词设计与 prompt caching 的官方指南.

---

## Chapter 6: 上下文管理

- Liu, N.F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2024). "Lost in the Middle: How Language Models Use Long Contexts." *TACL 2024*. https://arxiv.org/abs/2307.03172 — "大海捞针"问题的实验研究, 解释了为什么更大的上下文窗口不是万能解.
- Anthropic. "Long Context Tips." https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching — 长上下文使用的官方建议.

---

## Chapter 7: 子智能体

- Wang, L., Ma, C., Feng, X., Zhang, Z., Yang, H., Zhang, J., Chen, Z., Tang, J., Chen, X., Lin, Y., Zhao, W.X., Wei, Z., & Wen, J. (2024). "A Survey on Large Language Model based Autonomous Agents." *Frontiers of Computer Science, 18(6)*. https://arxiv.org/abs/2308.11432 — LLM 自主智能体的综合综述, 覆盖了子智能体委托模式.

---

## Chapter 8: 后台任务

- Python Software Foundation. "threading — Thread-based parallelism." https://docs.python.org/3/library/threading.html — Python 线程编程的官方文档, BackgroundManager 的实现基础.
- Python Software Foundation. "subprocess — Subprocess management." https://docs.python.org/3/library/subprocess.html — 子进程管理的官方文档.

---

## Chapter 9: 持久化任务

- Kahn, A.B. (1962). "Topological sorting of large networks." *Communications of the ACM, 5(11)*, 558-562. — 拓扑排序算法, DAG 任务依赖解析的理论基础.

---

## Chapter 10: 智能体团队

- Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B., Zhu, E., Jiang, L., Zhang, X., Zhang, S., Liu, J., Awadallah, A.H., White, R.W., Burger, D., & Wang, C. (2023). "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation." https://arxiv.org/abs/2308.08155 — 多智能体对话框架, 本章的持久化队友 + 邮箱通信模式与 AutoGen 的 Agent-to-Agent messaging 类似.

---

## Chapter 11: 团队协议

- Hoare, C.A.R. (1978). "Communicating Sequential Processes." *Communications of the ACM, 21(8)*, 666-677. — 通信顺序进程理论, 结构化通信协议的经典参考.

---

## Chapter 12: 自主智能体

- Hong, S., Zhuge, M., Chen, J., Zheng, X., Cheng, Y., Zhang, C., Wang, J., Wang, Z., Yau, S.K.S., Lin, Z., Zhou, L., Ran, C., Xiao, L., Wu, C., & Schmidhuber, J. (2024). "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework." *ICLR 2024*. https://arxiv.org/abs/2308.00352 — 多智能体自主协作框架, 队友自主认领任务的设计参考.

---

## Chapter 13: 工作隔离

- Git Documentation. "git-worktree — Manage multiple working trees." https://git-scm.com/docs/git-worktree — Git Worktree 的官方文档.

---

## Chapter 14: 安全与权限

- OWASP Foundation. "OWASP Top Ten." https://owasp.org/www-project-top-ten/ — Web 应用安全风险 Top 10, 安全层设计的参考框架.
- Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., & Fritz, M. (2023). "Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection." *AISec 2023*. https://arxiv.org/abs/2302.12173 — Prompt Injection 攻击的系统性研究.
- Anthropic. "Mitigating Prompt Injections." https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/mitigate-prompt-injections — Prompt Injection 防御的官方指南.

---

## Chapter 15: 可观测性

- OpenTelemetry. "OpenTelemetry Documentation." https://opentelemetry.io/docs/ — 可观测性标准, 本章的 Trace/Span 模型参考了 OpenTelemetry 的设计.
- Sridharan, C. *Distributed Systems Observability*. O'Reilly Media, 2018. — 分布式系统可观测性的入门读物.

---

## Chapter 16: 从 MiniAgent 到生产

### Agent 框架

- LangChain. "LangChain Documentation." https://python.langchain.com/ — 工具链 + 记忆 + Agent 的综合框架.
- LangGraph. "LangGraph Documentation." https://langchain-ai.github.io/langgraph/ — 基于图的 Agent 编排框架.
- Microsoft. "AutoGen." https://github.com/microsoft/autogen — 多智能体对话框架.
- CrewAI. "CrewAI Documentation." https://docs.crewai.com/ — 角色化多智能体团队框架.
- Anthropic. "Claude Code." https://docs.anthropic.com/en/docs/claude-code — MiniAgent 最接近的"生产版"参考.

### 部署与工程

- Liang, P., Bommasani, R., Lee, T., et al. (2023). "Holistic Evaluation of Language Models (HELM)." *Annals of the New York Academy of Sciences, 1525(1)*, 140-146. https://arxiv.org/abs/2211.09110 — 语言模型综合评估框架.
