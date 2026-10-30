# MacNativeGames Sequoia adaptations

用于 Apple Silicon / macOS Sequoia 15 的 Metal 3 适配补丁与构建记录。
目标是逐步提取多游戏共用的兼容能力；**当前只验证过以下两款游戏，不能直接转换任意 Switch 游戏。**

| 游戏 | 版本 | 基础源码 | 当前结果 |
|---|---|---|---|
| 王国之泪 | 1.2.1 | 社区 `m3-macos15` 分支，补充官方 1.2.1 支持 | 完成构建与本机验证；最终测试由用户进行 |
| 旷野之息 | 1.6.0，含两份 DLC | 官方固定提交，移入社区 Metal 3 后端并修正接口差异 | 用户确认修正间接资源声明后花屏消失，继续试玩中 |

测试环境：M1 Pro、16GB 内存、macOS 15.7.4。其他机器、长时间稳定性仍待验证。

## 使用

需要 Git；构建需要 Python 3.14、Xcode 命令行工具及各端口所需依赖。
先恢复对应源码，再阅读构建说明：

```sh
python3 scripts/prepare_source.py totk121 ../sources/totk121
# 或：
python3 scripts/prepare_source.py botw160 ../sources/botw160
```

- [王国之泪构建记录](docs/totk121-build.md)
- [旷野之息构建记录](docs/botw160-build.md)
- [其他 Switch 游戏适配流程](docs/other-switch-games.md)
- [新游戏需求模板](docs/game-request-template.md)
- [两款 App 的设置与按键](docs/controls-and-settings.md)
- [改动范围与验证记录](docs/changes.md)

`sources.json` 固定基础提交和补丁校验值。补丁针对指定提交，不能直接套到最新版上。
工作缓存与成品放在源码外。默认跳过启动检查，最终成品由用户打开测试。
排查需要运行游戏时应限时运行，结束后退出，避免持续耗电。

## 来源与限制

- [官方 MacNativeGames](https://github.com/ly05010419/MacNativeGames)
- [社区 Metal 3 / macOS 15 分支](https://github.com/1918662410-ship-it/MacNativeGames/tree/m3-macos15)
- TOTK 1.2.1 支持参考官方提交 `2db612bd7a82db2d94e3929556b71f0200f4b08c`。
- BOTW Metal 3 桥接参考社区提交 `6948e231b6dfc113b152baab40497db8501d8479`。

本仓库保存补丁、辅助脚本和说明。游戏程序、游戏资源、着色器代码、密钥、固件、系统字体、存档和成品 App 不在发布内容中。
构建使用用户自己合法持有的输入；原项目及依赖的许可证与署名仍须保留。
补丁基于 MIT 项目，许可见 [LICENSE](LICENSE)，第三方组件沿用其自己的许可。

这项工作主要是兼容适配与流程改进，没有证实相对原项目的帧率提升。
旷野之息的 Metal 4 补帧和新时间抗锯齿路径关闭；空间放大与原游戏抗锯齿依照该端口可用能力处理。
