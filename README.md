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

Codex 云端环境准备阶段执行 `sh roles/cloud-setup.sh`，安装依赖后执行同一入口；脚本要求已提供 Python 3.11。环境只选择本仓库、保持仅本人使用，不添加正式发送凭据或本机数据。准备完成后保存并发布，再从已发布环境创建全新任务运行 `.venv/bin/python -B roles/validate_repository.py`。保存、发布和新任务通过分别确认。

## 角色源码布局

采集模块保持在仓库根目录；分析专属 reader 和部署入口位于 `analysis/`。共享模块及恢复工具只在根目录维护一份；分析目录中的相对符号链接供仓库内阅读和测试使用。导出时按文件映射生成普通文件，目标机器不依赖仓库外的代码目录。

```sh
python3 -B roles/export_role.py collector /absolute/new/collector-source
python3 -B roles/export_role.py analysis /absolute/new/analysis-source
```

目标目录必须不存在。导出只包含列明的源码、方法资料、配置样例和合成测试，不包含运行状态。安装 reader、Skill 或 collector 时使用相应部署说明，不整目录覆盖正在运行的代码和状态。`project-methods/` 提供分析目标项目的业务约定模板；实际账户事实仍只来自目标机器的本地文件。

## 获取与部署

本文测试和导出命令在仓库检出目录执行；导出目录中的单角色入口分别为 `roles/offline_tests.py` 和分析部署说明中的命令。

使用 HTTPS 获取私有仓库，在目标机器检出已验证并指定的完整提交。不要直接运行来源不明的最新分支，也不要把云端工作区未提交文件当作发布版本。角色部署仅在目标机器的 Codex 会话内进行；不提供跨机器调度或一键部署。

程序和配置可以从源码恢复；历史、游标、策略基线、待办及回执只能从对应机器的一致性备份恢复。云端、Git 和源码包都不保存真实业务运行状态。

## 资料归属

仓库中的框架、契约、必要方法资料和测试随源码一起审核。「投资-btc」项目保存角色概览、策略资料和已发布的仓库版本入口。项目中早先上传的独立脚本和源码 JSON 只作为历史快照，不覆盖仓库指定版本。

## 独立核心版本

完整策略、Skill、研究嗅探、状态、报告与恢复由私有仓库 `york6668/btc-core-strategy` 维护。本仓库以 `core/btc-core-strategy` submodule 固定提交；采集与 reader 仍由本仓库维护。

运行 `git submodule update --init core/btc-core-strategy` 取得核心。分析导出组合 reader/角色的 `roles/source-map.json` 与核心自己的 `export-manifest.json`，不重复维护核心文件清单。核心升级后运行 `python3 roles/validate_repository.py --role all`，包含完整核心与实际 reader 组合验证。云端仅作离线验证，模型、采集、发送、事实与数据仍在本机。
