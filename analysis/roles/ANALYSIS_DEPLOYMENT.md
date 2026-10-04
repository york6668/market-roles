# 分析角色：本地部署与恢复

框架版本 `2026.10.01.2`，代码以私有仓库 `york6668/market-roles` 的指定提交为准。新版 Codex 云端环境用于开发和离线验证。本地机器拥有数据、游标、证据、策略、研究上下文、投递状态、资产事实和登录。初始分析机为 `yorkdeMac-mini.local`；采集机绑定由采集角色另行维护。

## 当前运行位置与历史布局

实际运行以目标节点的 `node.json`、固定发布目录、Compose 配置、镜像和挂载为准。源码说明不保存机器的当前版本表；主机别名、同名路径和历史成功状态不能替代目标节点身份及本次操作核验。

Docker 节点通过宿主版本入口固定核心版本，reader 使用角色提交导出的只读源码与独立可写数据目录。`current` 仅在新运行进入时选择版本，既有运行与恢复继续其固定版本。宿主工具解释器、容器主解释器和历史冻结兼容解释器分别配置。兼容解释器由节点持久管理、固定版本并验证精确复算，不能长期依赖应用缓存路径。

旧宿主安装可能使用项目 `telegram_reader`、Application Support 下的 reader venv、LaunchAgent 和 `.strategy` 链接。这些是历史布局示例，不能覆盖当前节点配置。迁移保留其游标、数据库、事实和恢复依赖；源码与数据根分别确认，不能以源码只读为由使嵌套数据挂载不可写。

## 参考源码与本机配置

`analysis-contract.json` 不包含机器路径。`machine-analysis.example.json` 是本机路径示例，没有凭据值。重建时修改自己的机器配置；`project_dir`、`skill_dir`、reader 数据与证据位置相互独立。`python` 用于本机工具及 reader 候选服务，可选择已安装 keyring 的 reader venv；策略生产入口使用节点选定的解释器或 Docker 转发入口。不同 Python 的浮点求和不能改写冻结原始字节，需要兼容时在 `frozen_market_python` 指向节点持久管理的解释器，并以 `frozen_market_python_version` 固定已验证版本。

参考 JSON 格式为 `market-role-source-v1`，`role=analysis`。源码按显式文件表选择；排除 `.strategy`、数据库、日志、真实市场附件、个人事实文件、凭据、Codex 登录、自动任务 memory/history、旧真实报告 fixture 和 rollback 资料。合成测试状态由 `roles/generate_synthetic.py` 调用核心构造程序在临时目录生成，不随源码保存或导出。

优先从指定 Git 提交导出，只写新目录，既不安装服务，也不开始分析或发送：

```sh
python3 roles/export_role.py analysis /absolute/new/reference
```

参考布局为 `telegram_reader/`、`skill/btc-core-strategy/`、`project-methods/`、`roles/`。可将当前 Skill 放入本机用户 skills 目录，或先通过本机配置指向参考目录做验证。方法引用相对实际 Skill 位置生成。内容 revision 1–7 原样兼容读取，新运行按 revision 7 方法准备；正式状态只有经过实际评估与采纳才进入新内容版本。保留原 `write-policy.json` 和运行上下文，不从旧叙述、rollback 或历史配置建议补造风险评估。沿现有小时任务跟踪个人风险和报告消费的实际覆盖，不因安装或离线测试通过关闭自然验收。

只读检查与真实策略入口：

```sh
/usr/bin/python3 roles/analysis_role.py --config /absolute/machine.json check
/usr/bin/python3 roles/analysis_role.py --config /absolute/machine.json strategy -- pin
```

`check` 只检查文件和路径，不确认凭据有效、市场判断完成或实际送达。`strategy` 将项目及状态根交给原 `strategy_v4.py`；不会生成模型判断，不会查询私有账户，也没有发送器。

## reader 与 Codex 任务分别恢复

reader 需要本机 Python 3.9+ 和 `keyring==25.7.0`。原机器 venv 直接复用；新机器在目标 reader 位置建立 venv 后按 `telegram_reader/requirements.txt` 安装。登录和 token 单独在本机准备，不从云端或源码 JSON 取回。不要再次 configure 清空或替换已恢复的频道绑定和游标。

新安装可以用以下命令生成候选 plist（仅生成，未安装）：

```sh
/usr/bin/python3 roles/analysis_role.py --config /absolute/machine.json render-reader /absolute/candidate.plist
```

候选保留每小时第 10 分钟，不增加 `RunAtLoad`/`KeepAlive`。helper 运行 reader；候选中只有路径变量，不嵌入 token。通过 `launchctl bootstrap gui/<uid> <plist>` 安装 reader，原服务回滚使用保存的原 plist 和原代码。修改既有机器时只替换确有变化的运行模块，保留原 plist、venv、数据、Keychain 和项目链接；等待下一次自然运行，不额外真实推送。

Codex 分析继续用原本地小时任务和原云端报告目的地。源码文件、普通 launchd 或 Python 不构成一个模型分析自动任务。沿用 Sol/high 与 Skill 内 Astra/max 分工。任务查询、暂停、恢复和路径调整通过 Codex 的原生任务工具或界面；禁止手写/改写 `automation.toml`。恢复时保留原 prompt、频率、模型、推理强度、项目和仅失败通知设置，不创建第二个 BTC 主任务，也不修改独立重大事件任务。新机器须先完成本机 Codex 登录、项目与目的地选择；静态参考包不能恢复这些登录和会话权限。[OpenAI 官方调度说明](https://learn.chatgpt.com/docs/automations?surface=app)也要求涉及本地文件时保持机器和应用运行。

## 完整状态恢复集合

下面均为私有本地备份内容，不进入参考源码包或云端：

- reader 的真实 `data/` 整个目录：`messages.sqlite3` 的频道绑定、正文审计、游标和同步状态；`collector_evidence.sqlite3` 的原始消息版本、附件、blob、校验历史、待下载和重试时间。包含 SQLite WAL/SHM 中已提交内容，不能只复制主数据库。
- 项目 `.strategy/` 整个真实目录：版本、`current`、所有公开证据原始字节、观察/成功深评/实际报告基线、SQLite、sensing、run 模板/intent/receipt、研究请求/候选/结果/进度、outbox 所有 artifact/status/attempt/request/receipt、报告复核、日报及运行缺陷状态。不能只备份 current 或当前报告。
- 三份用户事实文件、当前 `价值因子.md`、reader 的 `策略证据.md`；事实仅按原件恢复，价格或恢复动作不改变 `position_fact`。
- 本机任务 `memory.md` 和原 history（含其引用的待办/缺陷上下文）。原任务配置仅在本机留存用于原生工具恢复字段，不能成为云端参考文件，也不覆盖新任务目录的 `automation.toml`。
- 仍被研究请求、审阅或未知投递引用的本机 Codex rollout/附件/读取证据原件。用 `analysis_role.py recovery-inputs` 列出策略 JSON 引用的外部绝对文件，核对缺失项，再按本机配置添加独立 `state_paths`。不要上传完整 `.codex` 或账户登录库；无法找回的回读材料保持 UNKNOWN。
- 原 LaunchAgent、reader 与工具的本机解释器依赖、Keychain/Codex 登录分别按各自本机恢复方式保存或重新建立；它们不是模型策略状态。

机器示例列出的根均为真实目录或普通文件；不把整个项目当状态包。工程顶层链接在恢复后由 `link-project` 重建（遇到已有内容拒绝覆盖）。该命令不会向共享源码目录写入 data 链接，reader 和策略通过本机配置读取真实数据路径。

## 先停止所有写入者，再备份

通过 Codex 原生界面或工具暂停唯一 BTC 小时任务，并确认已经开始的小时工作/研究写入已结束。任务处于 PAUSED 不证明既有运行已经结束。也要停止手动策略写入。

对 reader 执行 `launchctl bootout gui/<uid>/local.btc.telegram-reader`，并确认没有该入口仍在同步。保留配置和数据。若本机 pipeline-audit/watchdog 会写入所选备份目录，也暂停它们并待进程退出；其他独立任务不受此操作影响。禁止在写入过程中把可能一致的快照当成完整恢复备份。

之后运行：

```sh
/usr/bin/python3 roles/role_support.py snapshot --config /absolute/machine.json /absolute/private-backup
```

helper 取得已存在的 writer lock，并比较复制前后状态；数据库只在副本里恢复已提交 WAL、检查完整性。它不自动暂停 Codex 任务，不能用一次成功锁定代替停止全部写入者。源码包与私有状态包分开保存。

## 恢复与回滚

保持 reader、模型任务和手动写入停止；将新本机配置的所有目标留为未占用路径。状态根不能重叠，不与现有运行合并：

```sh
/usr/bin/python3 roles/role_support.py restore --config /absolute/machine.json /absolute/private-backup
/usr/bin/python3 roles/analysis_role.py --config /absolute/machine.json link-project
/usr/bin/python3 roles/analysis_role.py --config /absolute/machine.json strategy -- recover
```

helper 保留状态根内部链接并将绝对内部链接规范为相对链接，恢复后指向新根；外部链接拒绝备份。只复制到新位置，复制中断清理本次新建内容，已有备份和旧运行仍保留。

原 run/research 的密封 JSON 可能绑定绝对路径、agent/turn/回读身份。完整接续优先在新机器保持原项目及相关引用的绝对路径；helper 只搬文件及内部链接，不改写密封 JSON、不更改 hash，也不重绑历史请求。可在本机配置将新源码放在任意位置，历史状态路径仍保持原值。若改变历史状态根，当前版本和队列可只读清点，原 run 不能冒充已迁移或静默重新执行；由 Codex 依据保留基线准备新的当前材料，逐项接续缺口。本次同路径完整恢复以及异路径 WAL/内部链接恢复分别经过合成测试，不宣称异路径密封上下文自动迁移完成。

对照原 `recover`：当前版本、观察及成功基线、研究待办、待发送、已完成投递、每个未知 attempt 应保持原身份和内容。UNKNOWN 不重置为 PENDING，不仅凭服务重启判定未发送，不重发旧正文。恢复后先对原 request/assistant 做实际回读，或按当前证据处理新的重要报告；仍无回读材料保留未知。已完成观察用原 intent/receipt 重放，不能为了恢复再产生一个新 observation。

回滚先再次停止有关写入者，恢复保存的原代码和 plist；已写状态保留，不用旧快照覆盖后续有效写入。确需回滚状态时在新的空目标恢复一致的完整备份，先核对这段时间的事实、观察与真实投递差异。reader 与 Codex 任务分别恢复，先 reader 的自然同步，再让模型任务读取已确认的本地材料。

## 附件修复边界与验收

已定位的一类 `attachment_unavailable` 来自历史附件积压占满单轮 20 件下载预算。判断此问题时按本地正文、附件、消费游标和下载状态核对，不把来源质量缺口误判为传输问题；现有冻结材料不回填、旧缺口不抹除。真实消息身份和自然运行证据保留在节点本地。

修复让每个标的最新报告的待下载附件优先进入同一个 20 件有界预算，其余待办保留并继续按原顺序处理；失败重试时间不绕过，来源质量不放宽。reader gap 导出含正文/附件身份和下载状态，策略冻结保留必要 report/bundle/transport 身份，排除 file_id、chat_id、采集 prose；身份不能提升事实可信度。VOO 的代理关系、UNKNOWN 复权与质量缺口不修成可分析。

离线验收使用合成数据和临时目录，禁真实网络、凭据、发送和生产调度。通过参考包解包后运行 `roles/verify_analysis_reference.py`；它分别验证 reader、身份冻结和真实策略入口，包含 revision 7 market→observe 与 revision 5 正式状态保留、同一观察恢复、SQLite/WAL、内部链接、游标、研究待办和 PENDING/UNKNOWN/DELIVERED 保留。组合验证另运行导出的完整核心测试，覆盖 revision 7 的独立风险结果、可选建议、原有机会分析及报告绑定。结果只证明源码与恢复接口；实际模型判断、真实发送、云端发布和自然小时运行各自需要实际证据。

## 独立核心发布

核心版本由 `core/btc-core-strategy` 的 Git 提交确定。使用核心的 `scripts/release.py` 与本机节点配置安装，正式模板见核心 `tasks/hourly.md`，恢复方式见 Skill 的 `references/releases.md`。Skill、代码、方法和测试一起发布，不单独复制 Skill 文件夹。旧 `build_analysis_reference.py` 仍可生成角色源码包，但改从本仓库及固定 submodule 导出，不读取资产项目中的核心副本。
