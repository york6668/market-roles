# market-roles

采集与分析角色的统一源码。GitHub 私有仓库为 `york6668/market-roles`；新版 Codex 云端环境为 `market-roles`。云端用于代码维护和离线测试，两台 Mac mini 独立运行正式服务。

## 入口

- [统一角色框架](roles/MARKET_ROLE_FRAMEWORK.md)：职责、数据契约、部署与状态恢复。
- [采集配置样例](roles/collector.example.json)：仅为样例，部署前生成本机配置。
- [分析部署与恢复](analysis/roles/ANALYSIS_DEPLOYMENT.md)、[分析配置样例](analysis/roles/machine-analysis.example.json)。
- [分析方法 Skill](core/btc-core-strategy/skill/btc-core-strategy/SKILL.md)：随版本维护，不依赖云端继承本机个人 Skill。
- `roles/role_support.py`：本机配置检查、服务预览、源码备用快照和状态备份恢复。
- `roles/export_role.py`：按 `roles/source-map.json` 的显式文件集合导出角色。

## 本地与云端测试

正式节点保持 Python 3.9 兼容，云端使用 Python 3.11。为测试创建独立虚拟环境：

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -B roles/validate_repository.py
```

现有 Mac 环境可用其已安装的 Python 3.9 运行同一离线入口。该入口先验证导出工具，再分别导出两种角色到临时目录，运行采集测试、reader 测试及真实 `strategy_v4.py` 的合成恢复测试。`--role collector` 或 `--role analysis` 可缩小到受影响角色。测试使用临时状态、空发送凭据并阻断出站网络。真实服务、launchd、正式 reader 消费和 Codex 自动任务只在对应 Mac 上验证。

Codex 云端环境准备阶段默认执行 `sh roles/cloud-setup.sh`，安装依赖并运行两角色的离线验证，明确报告数据服务尚未验证。需要完整数据服务验证时执行 `sh roles/cloud-setup.sh --with-data-service`，该模式要求 Python 3.11、Docker daemon 和 Compose 实际可用，并启动隔离 MySQL 8.4；缺项明确失败，不静默跳过。环境只选择本仓库、保持原访问范围，不添加正式发送凭据或本机数据。准备完成后保存并发布，再从已发布环境创建全新任务运行 `.venv/bin/python -B roles/validate_repository.py --with-data-service`。保存、发布和新任务通过分别确认。新任务先读本仓库 AGENTS、框架及对应核心方法，并核对当前仓库提交、核心 submodule 提交、实际方法入口和依赖；不得用旧任务结果代替新环境生效。

## 角色源码布局

采集源码由独立 `york6668/market-collector` 维护，`core/market-collector` 固定其提交，采集导出使用该核心自己的文件表。分析专属 reader 和部署入口位于 `analysis/`；ETF 共享证据契约也从同一固定采集版本导出，reader 的接收时间、失败记录和节点桥接实现继续保留在本仓。分析目录中的相对符号链接供仓库内阅读和测试使用。导出时按文件映射生成普通文件，目标机器不依赖仓库外的代码目录。

```sh
python3 -B roles/export_role.py collector /absolute/new/collector-source
python3 -B roles/export_role.py analysis /absolute/new/analysis-source
```

目标目录必须不存在。导出只包含列明的源码、方法资料、配置样例、测试程序与样本构造逻辑；合成测试数据在临时目录生成，不导出数据文件或运行状态。安装 reader、Skill 或 collector 时使用相应部署说明，不整目录覆盖正在运行的代码和状态。`project-methods/` 提供分析目标项目的业务约定模板；实际账户事实仍只来自目标机器的本地文件。

## 获取与部署

本文测试和导出命令在仓库检出目录执行；导出目录中的单角色入口分别为 `roles/offline_tests.py` 和分析部署说明中的命令。

使用 HTTPS 获取私有仓库，在目标机器检出已验证并指定的完整提交。不要直接运行来源不明的最新分支，也不要把云端工作区未提交文件当作发布版本。角色部署仅在目标机器的 Codex 会话内进行；不提供跨机器调度或一键部署。

程序和配置可以从源码恢复；历史、游标、策略基线、待办及回执只能从对应机器的一致性备份恢复。云端、Git 和源码包都不保存真实业务运行状态。

## 资料归属

仓库中的框架、契约、必要方法资料和测试随源码一起审核。「投资-btc」项目保存角色概览、策略资料和已发布的仓库版本入口。项目中早先上传的独立脚本和源码 JSON 只作为历史快照，不覆盖仓库指定版本。

## 独立核心版本

完整策略、Skill、研究嗅探、状态、报告与恢复由私有仓库 `york6668/btc-core-strategy` 维护。本仓库以 `core/btc-core-strategy` submodule 固定提交；reader 由本仓库维护，采集与 ETF 共享证据来自固定 `core/market-collector`。

运行 `git submodule update --init core/btc-core-strategy core/market-collector` 取得固定依赖，复用当前环境已有的 GitHub 认证。分析导出组合 reader/角色的 `roles/source-map.json` 与核心自己的 `export-manifest.json`，不重复维护核心文件清单。核心升级后运行 `python3 roles/validate_repository.py --role all`，包含完整核心与实际 reader 组合验证。云端仅作离线验证，模型、采集、发送、事实与数据仍在本机。ETF 匿名持仓及 TFTC 美元流量更新先安装 reader 共享契约，再更新采集端；保持节点状态与小时调度，通过自然运行核验。

核心候选新入口使用 content revision 9，在既有 Owner 中完成投资者政策、独立市场、组合风险与机会的总体取舍，并按实际版本交给报告和后续复核。生产采用版本由节点 current 实际指针确认；源码候选不等于已采用。风险结论可以独立成立，需要应对时再附建议；原有机会分析继续保留。旧正式状态、在办研究及 UNKNOWN 投递保留原身份，旧配置建议不自动解释为新风险评估。

## Docker 节点

两角色共用核心的 [Compose 与数据服务](core/btc-core-strategy/service/README.md)。`roles/containers/build.py collector|reader --docker <实际 Docker CLI> --tag <固定镜像标签>` 从源码白名单生成镜像，不复制运行数据。reader 由 `reader_bridge.py --config <现有节点配置>` 取用宿主 Keychain，经 stdin 执行原同步并在轮询前后保存 MySQL checkpoint。

检查点遇到核心明确的 `WRITER_BUSY` 时，在同一计划调用、同一阶段内最多尝试三次，间隔五秒；每次失败及最终结果分别记录。核心的 30 秒写入准入保持不变。其他错误立即失败，轮询始终只执行一次；轮询前未确认保存时不读取凭据、不推进 Telegram 游标，轮询后重试只保存状态，不重复拉取或发送。

采集节点先停止旧 writer，使用 `prepare_collector.py --node <原角色配置> --destination <新目录> --compose-file <核心 Compose> --image-tag <已验证版本>` 一致性备份、恢复和逐项核对实际 state_paths。该命令不采集、不发送、不启动服务；切换时仅启动 collector profile，保留原周期、公开来源和 Telegram 队列。回退必须停止容器并导出最新状态，UNKNOWN 不自动重发。首次及切换后恢复演练、实际运行、七个完整日本自然日的分析验收分别完成。
