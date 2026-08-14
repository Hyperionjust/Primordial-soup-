# TODO（发布前收口清单）

发布候选包已按四层结构交付并通过脱敏终检（见 `AUDIT-DESENSITIZATION.md`）。以下为如实记录的未完成/未验证项：

1. **已收口**：真实 DSH 运行时验证已完成（soup-memory skill 已安装至用户级技能目录并经指令级触发冒烟 11/11 PASS，含范围守卫负例与正例全流程；热重载链路实测见私有测试记录）。
2. **已收口（发布包级）**：对公开包做编译 + 样例冒烟（四脚本全 EXIT=0）；完整 20 用例私有回归套件的等价重跑仍建议在首个 release 前由维护者执行一次。
3. **已收口**：`py scripts\状态页生成器.py examples\mini-soup --stamp fixed` 已用**包内脚本**重生成（EXIT=0，关键数字全命中），发布包自包含验证通过。
4. **已收口**：git 仓库已初始化（`main`，root-commit a3dd117，27 文件），待推送 GitHub 远端；LICENSE 版权行为 `Copyright 2026 primordial-soup contributors`，若需具名作者可 amend。
5. **脚本注释级清洗的偏差说明**：四脚本非 100% 原样复制——红线强制清理了注释/字符串中的裁定者旧代号、私有包代号、宿主专属技能目录名、私有库提及（共 6 类 20 余处，见 AUDIT 第二节）；其中 `状态页生成器.py` 的技能目录扫描由宿主专属目录改为通用约定 `.agents/skills`（语义等价，样例输出不变）。行为逻辑零改动。
6. **README 链接验证**：`examples/GETTING-STARTED.md` 等相对链接未在 GitHub 渲染环境核对（本地均为相对路径，理论上有效）。
