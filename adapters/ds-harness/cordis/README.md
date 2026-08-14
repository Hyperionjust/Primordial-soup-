# @hyperionjust/primordial-soup-dsh

DSH cordis 插件：把 [primordial-soup](https://github.com/Hyperionjust/Primordial-soup-)（首个撞击式记忆系统）以官方 npm 通道装进 DeepSeek Harness。

**它只做一件事**：注册 `soup-memory` skill（运行时注册）——装这个包，机制指令集就绪，不用手动放 SKILL.md。跑脚本、登记台账、写卡等动作，由模型按 skill 指令用会话里**现成的 pwsh/bash 工具**完成，本插件不重复造工具。

- `user-invocable`（不随窗口默认加载，用户显式点名「闪电/抽卡」「沉淀/存卡」才进场）
- 范围守卫：仅当工作区是汤根（存在 `_氨基酸库/INDEX.md`）才生效

## 安装

在 agent preset 的 `cordis.yml` 加一行（消费 host `skills` registry、不 publish service，**无需 isolate realm**）：

```yaml
- id: soup-skill
  name: '@hyperionjust/primordial-soup-dsh'
```

前提：composition 已挂载 `@deepseek-ai/dsh-skill`（skill registry，host 侧）与 `@deepseek-ai/dsh-tool-skill`（skill 加载工具）。

## 用法

1. 用户说「闪电 / 抽卡」→ 模型加载 `soup-memory` skill；
2. 按 skill 正文 T1-T6 执行：跑抽样器（用 pwsh 工具跑 GitHub 仓库的 `scripts/闪电抽样器.py`，root 走 argv、位置无关）→ 碰撞 → 呈现闸门 → 台账登记 → 沉淀。

脚本从 [primordial-soup 仓库](https://github.com/Hyperionjust/Primordial-soup-) 的 `scripts/` 获取（宿主无关，随汤根或随仓库分发均可），本插件不含脚本——skill 只是指令，不是运行时。

## 待实测

插件本体（skill 运行时注册）未在真实 cordis composition 挂载验证，需在 DSH 会话里 `standingKeyFor` 或实际挂载一次确认。

## 与文件形式安装的关系

等价、不同通道：文件形式＝把 `adapters/ds-harness/SKILL.md` 放到 `~/.dsh/skills/`（watcher 发现）；本插件＝npm 安装 + composition 挂载（运行时注册）。选一即可，本插件是官方 npm 生态通道。
