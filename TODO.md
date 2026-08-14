# TODO（发布前收口清单）

发布候选包已按四层结构交付并通过脱敏终检（见 `AUDIT-DESENSITIZATION.md`）。以下为如实记录的未完成/未验证项：

1. **未做真实 DSH 运行时验证**：公开包未在真实 DSH 环境实测 skill 发现/热重载/交互确认工具链路（`adapters/ds-harness/INSTALL.md` 引用的 11/11 发现实证来自私有测试记录）。建议发布前在真实 DSH workspace 安放 `adapters/ds-harness/SKILL.md` 冒烟一次。
2. **未跑完整回归套件**：本次仅对四脚本做 `py_compile` + 合成样例冒烟（全 EXIT=0）；私有测试套件（20 用例、seed 复现快照比对、边界负例断言）未对公开包整体重跑。建议发布前对公开包重跑一遍等价回归。
3. **样例汤状态页未重生成**：`examples/mini-soup/_氨基酸库/状态页.html` 为清洗版（内嵌 RAW 中裁定列头已中性化）。可选收口：`py scripts\状态页生成器.py examples\mini-soup --stamp fixed` 重生成，与清洗后的台账/INDEX 完全一致（会覆盖样例产物，属预期）。
4. **git 仓库未初始化**：任务范围未含建仓。新仓库拍板后需：`git init`、首提交、推 GitHub 远端；LICENSE 版权行 `Copyright 2026 primordial-soup contributors` 若需具名作者，发布前由用户确认。
5. **脚本注释级清洗的偏差说明**：四脚本非 100% 原样复制——红线强制清理了注释/字符串中的裁定者旧代号、私有包代号、宿主专属技能目录名、私有库提及（共 6 类 20 余处，见 AUDIT 第二节）；其中 `状态页生成器.py` 的技能目录扫描由宿主专属目录改为通用约定 `.agents/skills`（语义等价，样例输出不变）。行为逻辑零改动。
6. **README 链接验证**：`examples/GETTING-STARTED.md` 等相对链接未在 GitHub 渲染环境核对（本地均为相对路径，理论上有效）。
