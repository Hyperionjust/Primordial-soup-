# soup-memory（DSH 版）安装说明

> 本包内容：`adapters/ds-harness/SKILL.md`（skill 本体，触发规则 T1-T6 内嵌正文）、`scripts/`（四个脚本：闪电抽样器.py / 状态页生成器.py / 潮汐周报生成器.py / M5结算脚本.py）、`spec/lightning-trigger.md`（触发点设计定稿，与 SKILL 正文 T1-T6 一一对应）。
> 依据：机制规范（`spec/SOUP-MECHANISM.md`）、触发点设计（`spec/lightning-trigger.md`）、移植笔记（`adapters/ds-harness/PORTING-NOTES.md`）。

## 1. 安放位（二选一）

DSH skill 发现要求**两层结构** `<root>/<name>/SKILL.md`（name 必须与 frontmatter `name` 一致，即 `soup-memory`）。

- **项目级（推荐起步）**：复制 `adapters/ds-harness/SKILL.md` 到任意 workspace 根下的 `.agents\skills\` 内，即：

  ```
  <workspace>\.agents\skills\soup-memory\SKILL.md
  ```

  随项目走，不污染全局；冒烟验证时直接复制到夹具 workspace 根即可。

- **全局**：复制到用户级 skill 目录：

  ```
  ~\.dsh\skills\soup-memory\SKILL.md
  ```

  对所有 workspace 生效（配合「范围守卫」按 `_氨基酸库/INDEX.md` 存在性自判，跨项目安全）。

- **frontmatter 注意**：DSH 路由只渲染 `name`/`description`（英文 "Use when …" 句式为路由信号），`whenToUse` 不进目录、无自动触发钩子——触发规则以正文「触发点（T1-T6）」为准。**description 是 YAML：正文含冒号（`:`）时值必须加双引号**——未加引号的普通标量含「冒号+空格」会被 YAML 解析为嵌套映射、整个 skill 在发现阶段被静默跳过（移植实证发现 22，真实发现实证揪出）。本版含 `disable-model-invocation: true` + `user-invocable: true`（**用户裁定：不随窗口默认加载**）——模型不会每次窗口自动加载，由用户显式点名（「闪电/抽卡」「沉淀/存卡」「合成：<scope>」「结案：…」）或经 tool-skill 显式调用入口（前导 `/soup-memory`）加载；加载后按正文 T1-T6 执行。发现实证：适配包测试套件 11/11 PASS（用户根发现、模型目录正确排除、项目根 `.agents\skills` 优先、完整加载）。

## 2. 热重载

DSH 的 skill 目录带 **watcher 热重载**：修改 `SKILL.md` 保存即生效，无需重启会话、无需重建任何产物；新会话与续接会话均按最新版渲染。**本包已实测**（2026-08-14）：修复全局安装 frontmatter 后，运行中的会话经 watcher 直接热加载，Web GUI skill 目录即时出现该条目（用户确认），无需重启。若改动未生效，检查 watcher 进程是否存活——注意 `pnpm run dev:web` 只负责 client-plugin/Web 产物重建，与 skill 热重载无关（本包不含 client-plugin，无需 dev server）。

## 3. 脚本分发两模式

- **模式 A：脚本随汤根分发（推荐）**——把 `scripts/` 下需要的脚本放进汤根的 `_氨基酸库\`（及对应机制目录），SKILL 正文命令按 `_氨基酸库\<脚本>.py "<汤根绝对路径>"` 调用。脚本一律以汤根目录作 argv、位置无关（不依赖 `cd`/工作目录），夹具与真实库通用；skill 目录与脚本解耦，换库不换 skill。
- **模式 B：脚本随适配包分发**——脚本留在 `scripts/` 旁，调用时把命令模板里的 `_氨基酸库\闪电抽样器.py` 换成适配包 scripts 目录内绝对路径。SKILL 正文不硬编码安装位，正文命令模板按模式 A 书写；用模式 B 时在调用处替换脚本路径即可。

路径含空格与中文（如 Windows 下的工作区绝对路径、`_氨基酸库`），一律带双引号；Python 解释器按 `py` → `python` → `python3` 顺序探测（Windows 通常无 `python3`，实测 `py` 可用）。

## 4. 改造后脚本新参数速查

| 脚本 | 参数 | 说明 |
|---|---|---|
| 闪电抽样器.py | `root`（必填） | 汤根绝对路径；只读，零副作用 |
| | `--exclude 文件夹名` | 抽样前移除，可多次；Resolver 三级匹配（精确→前缀无关→子串唯一） |
| | `--seed 整数` | 随机种子；不给则系统熵（打印提示复现命令）——复现测试/冒烟断言靠它 |
| | `--n 整数` | 抽取数，默认 3 |
| | `--hebb 浮点`（默认 2.0） | 赫布认可权重 |
| | `--zeig-closed 浮点`（默认 0.5） | 蔡格尼克保温 |
| | `--decay 浮点`（默认 0.7） | 遗忘衰减 |
| | `--floor 浮点`（默认 0.1） | 权重下限 |
| | `--min-rows 整数`（默认 10） | 台账数据行 < 该值 → 退化均匀抽样 |
| | `--strict` | 校验 INDEX 数据行数 == 磁盘卡文件夹数（蛋白质不进 INDEX） |
| 状态页生成器.py | `root`（必填）+ 可选 `[输出html路径]` + `--stamp` | 默认输出 `<root>\_氨基酸库\状态页.html`；`--stamp "YYYY-MM-DD HH:MM"` 固定时间戳、`--stamp fixed` 简写、缺省=now 保持原行为——供确定性重建与快照比对 |
| M5结算脚本.py | `root`（必填）+ `--sampler 路径` | 解释器 `sys.executable` 优先、兜底 py→python→python3 探测；spawn 失败/returncode 9009/stdout 空 → 明确报错（含实际 returncode 与提示句）；`--sampler` 显式指定抽样器（默认 `<root>\_氨基酸库\闪电抽样器.py` 保持兼容）；报告末尾含口径分叉提示行（卡级句式强认可不计入指标 2） |
| 潮汐周报生成器.py | `<周报md路径> [输出html路径]` | 可复用；字段行须 `- 【label】text` 形式；退出码 3＝对账缺失（HTML 仍写出，调用方按非零处理）；stdout/stderr 均 UTF-8 |

默认值即机制既定常量：不带参数的行为与规范默认一致。权重合成公式结构、呈现闸门四条增量判据、静默可审计、双向回写只追加、Resolver 三级匹配为机制本体，未参数化。

## 5. 冒烟验证指引

- **夹具**：本仓库 `examples/mini-soup/`（仿真汤根：`_氨基酸库\INDEX.md`、闪电台账.md、产品台账.md、氨基酸模板.md、蛋白质：测试簇.md + 6 个对话文件夹/卡，路径含空格与中文，正好压测引号/编码）。边界用例：空目录（友好报错）、缺台账（友好报错，非 traceback）、无 INDEX（照常跑通；`--strict` 下报错）、M5 结算汤根。
- **命令示例**（pwsh，解释器探测；`<适配包路径>`＝本仓库根，`<汤根绝对路径>`＝样例汤副本）：

  ```powershell
  py "<适配包路径>\scripts\闪电抽样器.py" "<汤根绝对路径>" --seed 1
  py "<适配包路径>\scripts\闪电抽样器.py" "<汤根绝对路径>" --seed 20260812 --hebb 2.0 --zeig-closed 0.5 --decay 0.7 --floor 0.1 --min-rows 10 --strict
  py "<适配包路径>\scripts\状态页生成器.py" "<汤根绝对路径>"
  py "<适配包路径>\scripts\M5结算脚本.py" "<汤根绝对路径>" --sampler "<适配包路径>\scripts\闪电抽样器.py"
  ```

- **预期**：抽样器 EXIT=0、同 seed 输出逐字节一致（可复现）、权重表按裁定句式打印、`--strict` 通过；状态页生成 `<汤根>\_氨基酸库\状态页.html`；M5 EXIT=0、指标与人工预推一致；潮汐对账 19/19 落页、UTF-8 stdout。适配包测试套件实测 20/20 PASS（四脚本全链路：加权+野卡、确定性 SHA256 全等、--strict、权重 CLI、--stamp fixed、M5 默认与 --sampler 双路径、9009/坏采样器明确报错、潮汐对账 + UTF-8；边界负例全部友好报错、零新文件）。
- **红线**：验证一律用合成样例（`examples/mini-soup/` 或自建测试汤），不触碰任何真实数据。
