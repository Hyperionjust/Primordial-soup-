# Primordial Soup — Release Announcement Package (v0.1.0)

> 用途：本文件为发布公告素材包，含 HN 英文稿、中文发布公告、仓库 About/Topics 建议与发布后 24 小时 checklist。所有宣称均锚定项目事实，未使用强度形容词。

---

## 1. Show HN 英文稿

**Title (≤80 chars):**

```
Show HN: A memory system that collides ideas instead of retrieving them
```

**Body (≤250 words):**

Every LLM memory system I know does the same thing: embed your past, retrieve what's semantically similar to now. Primordial Soup is an experiment in the opposite direction — it doesn't retrieve old ideas, it smashes old cards into new ones.

How it works: conversations distill into "amino acid cards" (a strong claim, its open questions, its connectable points). When you start a new session, a "lightning strike" draws 2 weighted-random cards plus 1 wild card — the model is forbidden from choosing them. If a card collides with your current topic and produces something that passes one of four gain criteria (changes a conclusion, creates counterexample tension, answers an old open question, opens a new direction), it's shown to you. Otherwise: complete silence.

Silence is auditable. Every draw is logged in a ledger, whether or not anything surfaced. You judge each collision on a four-level scale; strong approval doubles that card's Hebbian weight. Weights are computed by a script, not by the model. Periodically, an M5 settlement closes the books on two hard metrics (closed questions, strong approvals), and a "protein synthesis" step folds related cards into schematized reviews that re-enter the pool.

It's plain files plus a CLI — host-agnostic, Apache-2.0. The sample soup is fully synthetic, so you can try it in five minutes: https://github.com/Hyperionjust/Primordial-soup-

I surveyed the public ecosystem (semantic-retrieval + LLM-evolution systems like A-MEM; context-compaction systems like memory-compiler) and, as of August 2026, haven't found a public project combining random collision + weight evolution + synthesis + full audit. Happy to be proven wrong — that's the point of a falsifiable claim.

---

## 2. 中文发布公告（公众号/知乎风格）

**标题备选：**
- 「我做了个不检索的记忆系统：它靠随机碰撞」
- 「原始汤 Primordial Soup：让 AI 的旧想法撞出新东西」

**正文：**

过去一年，AI 记忆系统的主流路线几乎只有两条：一条是语义检索——把过去嵌入向量库，取出和此刻最像的；另一条是摘要压缩——把长对话压进上下文窗口。两条路线共享同一个假设：**相关的过去才值得被想起。**

「原始汤」（Primordial Soup）想检验一个相反的假设：也许真正值钱的新想法，恰恰来自和此刻**不相关**的旧想法。所以我做了一个撞击式记忆系统——它不检索旧想法，而是把旧卡片随机撞向当前话题，看能不能撞出新东西。

机制很简单。每次对话结束后，沉淀出几张「氨基酸卡」：一张卡 = 一个强观点 + 它的未解问题 + 它的可连接点。新会话开始时，一道「闪电」落下：脚本按权重随机抽 2 张卡，再加 1 张完全随机的野卡，撞向当前话题。碰撞产物必须通过四条增量判据之一——推翻旧结论、制造反例张力、回答悬而未决的旧问题、或开辟新方向——才有资格呈现给你。**过不了判据？那就完全静默。**

为什么是这四条？因为「看起来像新想法」太容易伪装了，我要的是可检验的增量。为什么是随机抽取而不是模型挑选？因为模型挑卡等于另一种检索，会把碰撞退化成相似性匹配。所以整个系统守五条纪律：

1. **真随机**——模型被禁止挑卡，抽卡由脚本完成；
2. **呈现闸门**——四条判据不过，一个字都不给你看；
3. **沉默可审计**——每一次抽取都登记台账，没呈现的那些也查得到；
4. **裁定权在你**——四档反馈，强认可才让该卡赫布权重 ×2，权重由脚本算，模型没有裁量权；
5. **只追加不改写**——历史记录不可篡改。

每隔一段时间，系统做一次 M5 结算，用两个硬指标交账：关闭了多少旧问题、拿到多少次强认可。活下来的卡片族还会被「蛋白质合成」折叠成图式化综述，重新入池——同族不同出。

整套东西就是纯文件加命令行，不绑定任何宿主，Apache-2.0 开源。仓库里的样例汤是全合成的，五分钟就能跑起来。调研锚定 2026 年 8 月的公开生态：随机碰撞 + 权重演化 + 蛋白质合成 + 全量审计这四层组合，我没见到同类——这个说法欢迎被证伪。

它不是检索的替代品，而是一个对照实验：当记忆系统放弃「相关性」这个拐杖，会发生什么？欢迎来撞一撞。

仓库：https://github.com/Hyperionjust/Primordial-soup-

---

## 3. 仓库 About + Topics 建议

**About（英文，用于 GitHub About 栏）：**

```
The first collision-based memory system: it doesn't retrieve old ideas — it smashes old cards into new ones.
```

**About（中文，用于 README 首行 / 中文渠道简介）：**

```
首个撞击式记忆系统：不检索旧想法，随机撞出新东西。
```

**Topics（8–10 个）：**

```
memory
agent-memory
cross-conversation-memory
serendipity
llm-agents
llm-memory
knowledge-management
hebbian-learning
emergence
cli-tool
```

---

## 4. 发布 Checklist（push 后 24 小时内）

**前置确认（push 前）**

- [ ] tag `v0.1.0` 已打并推送（`git tag v0.1.0 && git push --tags`）
- [ ] README 首行 About 已就位，仓库链接可公开访问
- [ ] GitHub 仓库 About 与 Topics 按第 3 节配置
- [ ] 样例汤跑通一遍，确认「五分钟上手」承诺成立

**T+0（push 后 0–2 小时）**

- [ ] **Show HN 发帖**：建议美东工作日 8:00–10:00（对应北京时间 20:00–22:00，夏令时）发，标题用第 1 节标题，正文原样贴出
- [ ] 首发回复话术（帖子发出后立刻自评一条，一句）：
  > "Happy to answer questions — and if you know a public project already doing random collision + weight evolution + full audit, I'd genuinely like to be pointed at it."
- [ ] **Reddit**：r/LocalLLaMA 或 r/MachineLearning（视版规，ML 通常不收 Show 帖，优先 LocalLLaMA），与 HN 错开 2–4 小时，避免同一时段分流讨论

**T+2–8 小时**

- [ ] HN 评论区值守：每条技术质疑在 1 小时内回应；回应口径只引机制与判据，不做强度宣称
- [ ] 中文渠道：**知乎**发专栏文章（第 2 节正文 + 标题备选一），**微信公众号**同步（标题备选二更口语）
- [ ] 掘金 / V2EX 发短帖：一句话定位 + 仓库链接 + 「沉默可审计」这一个差异点，不重复长文

**T+8–24 小时**

- [ ] 汇总首轮反馈：把「被证伪」类回复（指出同类项目）单独登记——这正是项目要的碰撞输入
- [ ] 若 HN 进入首页，准备一条置顶补充：M5 结算双硬指标的当前读数（如有）
- [ ] 所有外部讨论链接登记入项目台账（沉默可审计纪律延伸到发布侧：发了什么、在哪发、回应了什么，全部留痕）
