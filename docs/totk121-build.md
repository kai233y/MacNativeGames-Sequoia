# 《王国之泪》1.2.1：macOS Sequoia 打包流程

> 本文及 `build_totk121.py` 仅是 TOTK 1.2.1 专用案例。打包其他 Switch 游戏请使用同目录的 `Switch其他游戏Sequoia打包流程.md`，先确认目标游戏端口及适配要求，不要只替换本案例的游戏文件路径。

本流程整理于 2026-10-29，适用于这次的 **M1 Pro、16GB 内存、macOS 15.7.4**。目标是生成 **1.2.1 / Metal 3 / 最低 macOS 15.0** 的 App。

**后续交付约定：完成构建、数据完整性检查和签名校验即可，最终的打开、画面、性能及游玩测试由用户进行。不要自动运行游戏或启动额外成品测试。**

## 1. 保存好这些成果

这些文件均在本文所在的 `outputs` 目录中：

| 文件 | 用途 |
|---|---|
| `MacNativeGames-macos15/` | 已完成本次适配的源码，优先继续使用 |
| `build_totk121.py` | 复用入口，处理固件 ZIP 和临时密钥后调用构建脚本 |
| `macos15-v121-adaptation.patch` | 相对于原社区分支固定提交的完整适配补丁 |
| `MacNativeGames-macos15-adapted-source.zip` | 已适配源码快照，不含游戏、固件、密钥或构建缓存 |
| `Sequoia-build-validation.json` | 本次已有验证记录，不代表以后每次重新打包都自动运行成品测试 |
| `Tears of the Kingdom 1.2.1 Sequoia.app` | 本次成品，逻辑大小约 16.34 GiB |

**不要用原始社区分支覆盖已适配源码。** 原始 `m3-macos15` 分支没有直接支持这次的 1.2.1 组合。

## 2. 准备输入文件

| 输入 | 本次使用的内容 |
|---|---|
| 本体 | 《王国之泪》1.0.0 NSP，标题 ID `0100F2C0115B6000` |
| 更新 | 独立的 1.2.1 NSP，标题 ID `0100F2C0115B6800` |
| 密钥 | `prod.keys`；本次没有使用用户提供的独立 `title.keys` |
| 字体来源 | `Firmware.22.1.0…zip`，也可给解压后的 NCA 目录 |

密钥来自你本地提供的文件，脚本不会下载、输出或写入成品。NSP 的通用票据由构建工具从包内读取。

这套字体支持针对本次验证过的完整字体集合；更换固件时，文件可能相同，也可能需要另做兼容验证。不能只为通过构建而替换校验哈希。

## 3. 构建环境与磁盘

- Apple 芯片 Mac，macOS 15 或更高。
- Python 3.14，Xcode 命令行工具，以及 `/opt/homebrew` 下的 `opus`、`libvpx`。
- 首次构建需联网获取固定版本的 SPIRV-Cross、hactool 和 Python 依赖。
- 首次构建前，建议在游戏原文件之外再留 **约 60GB** 余量；脚本对本体加更新的最低空闲检查为 40GB。此次缓存中同时保留本体与更新后的数据，另有编译和着色器文件。
- 工作目录和 App 放在同一个 APFS 卷，可通过克隆共享大文件的数据块。放到不同卷时，要另外留出成品副本的空间。

只在缺少工具时安装：

```sh
xcode-select --install
HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 brew install opus libvpx python@3.14
```

已安装完整 Xcode 且命令行工具选择正确时，不必重复安装。构建本身不需要安装 Unicorn；那是本次额外补丁验证使用的工具。

## 4. 下次直接运行的命令

在终端执行以下命令；如果输入文件移动过，只修改对应路径：

```sh
python3.14 scripts/build_totk121.py \
  --source ../sources/totk121 --game /path/to/base.nsp \
  --update /path/to/update-1.2.1.nsp --keys /path/to/prod.keys \
  --firmware /path/to/firmware.zip --work ../build/totk121 \
  --out "../apps/Tears of the Kingdom 1.2.1.app"
```

先在命令末尾加 `--dry-run`，可以只检查路径、显示构建计划，不开始打包。

默认路径：

- 源码：复用脚本旁的 `MacNativeGames-macos15/`。
- 缓存：本文所在目录的上一级下的 `work/TOTK_build/`。
- 输出：复用脚本旁的 `Tears of the Kingdom 1.2.1 Sequoia.app`。

可以用 `--source`、`--work`、`--out` 改位置。工作目录与 App 必须在源码目录外。重新打包前先退出成品游戏；使用相同工作目录可复用已经完成并通过检查的步骤。

脚本会自动：

1. 从固件 ZIP 提取 NCA，或者使用给定的固件目录。
2. 从原 `prod.keys` 中选出 NCA 工具需要的、格式正确的派生密钥，存到权限为 `0600` 的临时文件，退出时删除。
3. 设置 `TOTK_M3=1`，调用已适配的 `build_app.py`。
4. 严格校验所选 1.2.1 的 ExeFS、改写代码，以及本体和合并数据的哈希；生成启动着色器。
5. 编译 Metal 3 版、装配 App、验证签名，并清除这份新生成本地 App 继承的隔离属性。
6. 使用 `--skip-launch-check` 结束构建，输出成品位置，**不启动 App**。

若中断或失败，先看 `work/TOTK_build/logs/` 中报错点名的日志，再用相同命令继续。没有日志变化时先确认进程是否仍在工作，不要同时开启第二次完整打包。

## 5. 本次遇到的问题及处理

| 问题 | 已采用的处理 |
|---|---|
| 上游主线要求 macOS 26 / Metal 4 | 使用社区 Metal 3 分支，构建时设置 `TOTK_M3=1` |
| 社区分支未支持 1.2.1 | 接入上游已发布的 1.2.1 哈希、版本地址、运行时表、资源覆盖和启动器支持，新增 `runtime-v121-m3` 目标 |
| 本体 NSP 的 `main.npdm` 与原卡带记录不同 | 更新版使用更新包的完整 ExeFS，仍严格校验更新包 NPDM；本体仅用于数据来源，其程序模块及最终数据哈希继续检查。未修改原本体校验清单 |
| Firmware 22.1.0 部分字体与旧记录不同 | 验证 NCA 文件系统头、六级 IVFC、字体各表及整个字体的校验和后，增加独立的完整字体集合清单；没有取消字体完整性检查 |
| hactool 报密钥字段长度错误 | 原文件中有与本次构建无关、长度异常的 KEK source 字段。只将需要的 `header_key`、`titlekek_XX`、`key_area_key_*_XX` 写入私有临时副本，原文件不变 |
| 启动时被 macOS 终止，签名静态检查却通过 | 新生成 App 根目录带 `com.apple.quarantine`。对已构建并验证签名的这份本地 App 清除该属性后，启动正常；修复已纳入打包脚本 |

如果将来必需的派生密钥字段本身错误，复用脚本会报错停止，不会猜测或截断密钥。字体或游戏数据出现未知哈希时也应先核实文件，而不是绕过校验。

## 6. 源码来源与恢复

- 社区仓库：`https://github.com/1918662410-ship-it/MacNativeGames`，分支 `m3-macos15`。
- 固定基础提交：`f71ea7b56eb1f7064d5e753428cc6b05a124241b`。
- 上游 1.2.1 支持参考提交：`2db612bd7a82db2d94e3929556b71f0200f4b08c`。

最方便的恢复方式是解压本文旁的 `MacNativeGames-macos15-adapted-source.zip`，将其中的源码目录与复用脚本放在一起。这个快照已包含适配，不必再应用补丁。

也可从干净仓库恢复：

```sh
git clone --branch m3-macos15 https://github.com/1918662410-ship-it/MacNativeGames.git MacNativeGames-macos15
git -C MacNativeGames-macos15 checkout --detach f71ea7b56eb1f7064d5e753428cc6b05a124241b
git -C MacNativeGames-macos15 apply --check /完整路径/macos15-v121-adaptation.patch
git -C MacNativeGames-macos15 apply /完整路径/macos15-v121-adaptation.patch
```

补丁仅应用到干净的固定基础版本；已适配目录不要再次应用。若基础提交有变化，应重新核对适配，不能直接假定旧补丁仍适用。

## 7. 本次结果与后续测试边界

本次已经完成：38 项项目单元测试、75 项帧率补丁检查、时间步补丁检查、22 个 Metal 3 图形目标文件零 Metal 4 未定义引用、签名校验、加载器与文件系统验证，以及两次原生启动验证。8,286 个启动着色器全部准备成功，无跳过。

曾观察到成品运行、导入启动着色器、进入首次 GPU 预热，并记录到音频及键盘输入。**这不等于完成了长时间游玩或稳定帧率验证。**

下次默认仅完成构建和静态校验。你自行双击成品，等待首次着色器预热后测试画面、声音、手柄、存档和性能。
