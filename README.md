# market-roles

采集与分析角色的统一源码。GitHub 源码仓库为 `york6668/market-roles`。Codex 执行环境按当前工作站入口发现；代码维护和离线测试与正式节点执行分别核验。

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

现有 Mac 环境可用其已安装的 Python 3.9 运行同一入口。它按现有映射和核心 manifest 导出所选角色，并检查 Python 语法；`--role collector` 或 `--role analysis` 可缩小范围。输出明确为源码检查，行为验证为 `NOT_RUN`，不执行包内程序、业务或旧测试。受影响行为另从当前有效契约和真实消费者确定临时验证，案例、断言、mock、夹具及构造程序不进入 Git 或正式包；所需状态、凭据、网络和副作用按本次验证范围隔离。真实服务与自然执行仍按目标节点的实际证据验收。

Codex 云端环境准备阶段可执行 `sh roles/cloud-setup.sh` 安装依赖并核源码导出及语法；它不执行行为或 Docker/MySQL 验证，旧 `--with-data-service` 请求明确返回未执行，不能降格为源码检查成功。需要数据服务验证时，由当前任务按受影响组合准备仓外临时验证，核实实际 Docker/Compose 等依赖并保留真实结果。环境不取得正式凭据或本机数据。新会话从当前项目入口核所选仓库、核心 gitlink、实际方法和职责；环境保存、发布、新会话采用、行为回归与正式运行分别确认，历史测试结果不成为新的部署条件。

## 角色源码布局

采集模块保持在仓库根目录；分析专属 reader 和部署入口位于 `analysis/`。共享模块及恢复工具只在根目录维护一份；分析目录中的相对符号链接供仓库内阅读和测试使用。导出时按文件映射生成普通文件，目标机器不依赖仓库外的代码目录。

```sh
python3 -B roles/export_role.py collector /absolute/new/collector-source
python3 -B roles/export_role.py analysis /absolute/new/analysis-source
```

目标目录必须不存在。导出只包含现有清单中有真实用途的正式源码、方法资料和配置样例；测试案例及其程序、夹具和构造逻辑不随正式包导出，节点数据与运行状态留在原环境。安装 reader、Skill 或 collector 时使用相应部署说明，不整目录覆盖正在运行的代码和状态。`project-methods/` 提供分析目标项目的业务约定模板；实际账户事实仍只来自目标机器的本地文件。

## 获取与部署

本文源码检查和导出命令在仓库检出目录执行；导出目录沿对应角色部署说明使用正式入口，不要求携带或恢复旧测试程序。

使用 HTTPS 获取仓库，在目标机器检出已验证并指定的完整提交。不要直接运行来源不明的最新分支，也不要把云端工作区未提交文件当作发布版本。角色部署仅在目标机器的 Codex 会话内进行；不提供跨机器调度或一键部署。

程序和配置可以从源码恢复；历史、游标、策略基线、待办及回执只能从对应机器的一致性备份恢复。云端、Git 和源码包都不保存真实业务运行状态。

## 资料归属

仓库中的框架、有效契约和必要方法资料随源码审核；验证结果保留当时输入、版本和条件，不形成新的业务契约或材料留存义务。「投资-btc」项目保存角色概览、策略资料和已发布的仓库版本入口。项目中早先上传的独立脚本和源码 JSON 只作为历史快照，不覆盖仓库指定版本。

## 独立核心版本

完整策略、Skill、研究嗅探、状态、报告与恢复由仓库 `york6668/btc-core-strategy` 维护。本仓库以 `core/btc-core-strategy` submodule 固定提交；采集与 reader 仍由本仓库维护。

运行 `git submodule update --init core/btc-core-strategy` 取得核心。分析导出组合 reader/角色的 `roles/source-map.json` 与核心自己的 `export-manifest.json`，不重复维护核心文件清单。核心升级后可运行 `python3 roles/validate_repository.py --role all` 核完整组合的导出与语法，再针对变化的真实 reader/核心接口作临时行为验证；源码检查不能签组合行为通过。云端工程环境用于离线验证；正式执行入口与运行数据由获准节点承载。本机执行不等于模型计算或材料处理仅在设备内，进入模型会话的内容及工具回传仍按现有授权和数据范围控制。

分析角色沿当前源码提交所固定的核心入口运行。可读格式取自该核心发布清单，实际评估、组合决定和报告格式由本轮入口返回。各组依据当期有效配置完成决定，结果沿原报告与复核流程消费。生产采用以节点和原运行的实际绑定核验。历史决定、在办研究及 UNKNOWN 投递沿其原身份处理。

## 固定来源与角色组合

源码身份以本次检出的完整提交为准，同时核对该提交的 `roles/source-map.json`、`core/` gitlink 和核心 `export-manifest.json`。默认分支、CI 快照、另一角色版本及节点已安装目录不能互相代替；`.gitmodules` 的 `branch` 字段也不能替代 gitlink 固定提交。

本提交的采集映射取自仓库根目录。选择含 `core/market-collector` 的其他角色提交时，采集及共享证据文件按该提交的映射和 collector gitlink 取源；不能把本 README 的目录布局套到另一固定版本。可用 `git ls-tree HEAD core/btc-core-strategy core/market-collector` 核对实际存在的依赖，仅初始化本提交已声明的 submodule，不用 `--remote` 隐式升级。

分析导出组合角色文件表与固定核心的导出清单，运行时配置与模型阅读的 Markdown 另有职责。导出候选应保留角色、依赖提交和文件身份；来源相同且验证适用的现有候选可复用。导出成功、独立核对、实际安装及运行采用分别确认，不能手工改写已冻结发布目录后继续声称原来源身份，也不能因 Reader 文档修正顺带切换节点核心。

## Docker 节点

两角色共用核心的 [Compose 与数据服务](core/btc-core-strategy/service/README.md)。`roles/containers/build.py collector|reader --docker <实际 Docker CLI> --tag <固定镜像标签>` 从源码白名单生成镜像，不复制运行数据。reader 由 `reader_bridge.py --config <现有节点配置>` 从原 Keychain 取用凭据并经 stdin 交给实际消费者。已配置 `docker_service.reader_backend=MYSQL_V1` 的节点调用现有 core 的 `reader-poll`；无该配置的独立旧部署仍沿原 reader profile/checkpoint 路径。核心来源更新不自动迁移节点数据、切换 backend 或启动轮询。

检查点遇到核心明确的 `WRITER_BUSY` 时，在同一计划调用、同一阶段内最多尝试三次，间隔五秒；每次失败及最终结果分别记录。核心的 30 秒写入准入保持不变。其他错误立即失败，轮询始终只执行一次；轮询前未确认保存时不读取凭据、不推进 Telegram 游标，轮询后重试只保存状态，不重复拉取或发送。

采集节点先停止旧 writer，使用 `prepare_collector.py --node <原角色配置> --destination <新目录> --compose-file <核心 Compose> --image-tag <已验证版本>` 一致性备份、恢复和逐项核对实际 state_paths。该命令不采集、不发送、不启动服务；切换时仅启动 collector profile，保留原周期、公开来源和 Telegram 队列。回退必须停止容器并导出最新状态，UNKNOWN 不自动重发。首次及切换后恢复演练、实际运行、七个完整日本自然日的分析验收分别完成。
