# DESIGN — cordis 插件实现决策记录

## 读到的 API 结论（harness 源码实证，行号可溯）

1. **skill 运行时注册**（`packages/skill/skill/src/index.ts`）：
   - `ctx.skills.register(skill)`：`SkillRegistration = { name, description, content, source, invocation?, whenToUse?, resourceBase?, metadata? }`。
   - `name` 必须 kebab-case（`^[a-z0-9]+(?:-[a-z0-9]+)*$`）——`soup-memory` 合法。
   - `source` 必需；`'bundled'` 是标准来源（`BUNDLED_SKILL_RANK=600`）。
   - `invocation` 缺省 `{modelInvocable:true, userInvocable:true}`；本包传 `{modelInvocable:false, userInvocable:true}`，精确对应文件形式 SKILL.md 的 `disable-model-invocation: true` + `user-invocable: true`。
   - 返回 disposer，Fiber 销毁自动注销；同层同名单先注册者胜。

2. **工具注册**（`packages/shell/tool-pwsh/src/index.ts`）：`ctx.tools.register(defineTool({...}))`；子进程必须走 `ctx.shell` service（executor seam），裸 child_process 撞沙盒 EPERM。——**本包最终未用**，见下。

## 设计取舍（含一次重要收敛）

- **最终形态：只注册 skill，不做工具。** 初版曾加 `soup_lightning` 工具（封装跑抽样器），后被判定为冗余：DSH 会话已有 `pwsh` 工具，模型按 skill 指令直接 `py scripts\闪电抽样器.py <root>` 即可，插件重复造工具违背"纯文件+CLI 本体不变"。
- **脚本不随包分发**：插件只携带 skill 指令（`skill-body.md`），脚本从 primordial-soup 仓库 `scripts/` 获取（宿主无关，随汤根或随仓库分发）。npm 包 = 指令集的挂载面，不是运行时。
- **不 publish service、无需 isolate realm**：skill register 是消费 host `skills` registry（软依赖 `ctx.get('skills')`，缺则空操作），一行挂载。

## 待实测项（本环境无 cordis 运行时工具）

1. 真实 composition 挂载 + `standingKeyFor` / 实际会话验证 skill 可见。
2. npm 发布（`npm publish`，需 token 与联网）——本环境仅做了 `npm pack --dry-run` 结构验证。
