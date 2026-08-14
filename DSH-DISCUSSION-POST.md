# primordial-soup — DSH 社区发布专稿

## 标题候选

1. **长会话、resume、fork 满天飞的时代，你的旧想法怎么撞上新问题？—— primordial-soup 的 DSH 适配版来了**
2. **给 DSH 装上"撞击式记忆"：primordial-soup 适配层发布，T1-T6 触发点为 DSH 会话模型重设计**

---

## 正文

DSH 用户大概都有这种体验：会话是长命的，可以随时 resume；fork 一个子代理，工作区还共享。这套模型对干活很友好，对"记忆"却很残酷——上一轮对话里那个闪过的想法，躺在某个 transcript 深处，等你下次需要它时，既不会有人提起，你也想不起来搜。检索式记忆系统能解决"记得找什么"，但解决不了"不知道自己忘了什么"。

primordial-soup（原始汤）是首个撞击式记忆系统：它不检索旧想法，而是随机撞出新东西。机制一句话：对话沉淀为"氨基酸卡"，新会话开场做一次闪电加权随机抽卡（2 张加权 + 1 张野卡，模型禁止挑卡），卡片与当前话题碰撞，过了四条增量判据才呈现，否则静默；用户四档裁定（强认可触发赫布加权 ×2），一切登记台账——连"沉默"都可审计。

### 为什么这对 DSH 特别适配

这不是把 Claude 版的钩子照搬过来，而是为 DSH 会话模型重设计的：

- **T1-T6 触发点重设计**：原版挂在"会话开始/结束"，但 DSH 会话长命、可 resume、fork 子代理共享工作区，原挂点直接不成立。重设计后的方案包括：首个实质问题 + 台账防重的双条件触发；fork/子代理豁免（防止父子双重登记）；goal complete 时提议沉淀；以及 ask_user_question 取消异常（ASK_CANCELLED / ASK_ABORTED）的回填待补机制。
- **适配层随仓库发布**：`adapters/ds-harness/` 内含 SKILL.md 技能全文、INSTALL.md 安装说明、PORTING-NOTES.md 移植清单，开箱即用。
- **全链路实测**：DSH/Windows 环境 9 用例冒烟全 PASS（确定性、权重数学、野卡均匀性、同族去重、范围守卫等）；skill 触发冒烟 11/11；脚本改造 R1-R7（解释器探测、9009 失败模式修复、--stamp 确定性等）。
- **触发裁定克制**：`disable-model-invocation: true`，不随窗口默认加载——你显式点名（"闪电/抽卡""沉淀/存卡"）它才进场，汤根判定的范围守卫优先级最高。

### 怎么试

纯文件 + 命令行，宿主无关，Apache-2.0。仓库：https://github.com/Hyperionjust/Primordial-soup- 。样例汤全合成，五分钟上手；DSH 安装路径见 `adapters/ds-harness/INSTALL.md`。

### 邀请

这套机制的有效性建立在一个可被证伪的假设上：随机碰撞能产生增量。2026-08 的调研与设计文档都在仓库里，台账格式公开。欢迎试用，更欢迎证伪——如果你的 DSH 会话里撞出来的都是噪声，请带着台账来打脸，这正是项目想要的反馈。

---

## English Summary (for cross-posting)

primordial-soup is a collision-based memory system: instead of retrieving old ideas, it randomly collides them with your current topic. Conversations condense into "amino acid cards"; each new session draws a lightning-weighted random hand (2 weighted + 1 wild card, model forbidden from picking), and only collisions passing four incremental-value gates are surfaced—silence is logged and auditable. The DSH adapter ships in-repo at `adapters/ds-harness/`, with triggers T1–T6 redesigned for DSH's long-lived, resumable, forkable session model (dedup guards, fork exemption, goal-complete prompts, ask-cancel backfill). Fully tested on DSH/Windows: 9/9 smoke cases, 11/11 skill-trigger checks. Files + CLI only, host-agnostic, Apache-2.0 — five minutes to try with the sample soup.

---

## 发帖建议

- **GitHub Discussions（英文区/主区）**：用英文摘要段开头 + 正文翻译要点，标题走机制向（"Collision-based memory for long-lived agent sessions"），附仓库链接。
- **DSH 中文社区/论坛**：直接贴本稿正文，标题用候选 1（痛点设问句更贴合中文社区阅读习惯）。
- **知乎/掘金等外溢渠道**：以"为什么检索式记忆不够"切入，把 T1-T6 重设计作为工程细节亮点单开一节，避免与已备中文稿重复。
