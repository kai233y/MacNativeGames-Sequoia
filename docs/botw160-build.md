# 旷野之息 1.6.0：Sequoia 构建记录

成品：同目录的 `Breath of the Wild 1.6.0 Sequoia.app`。

- 目标：Apple 芯片，macOS 15.0 及以上；Metal 3 后端。
- 内容：提供的 XCI 中的本体、1.6.0 更新和两份 DLC，均已按上游清单完成数据校验。
- 启动着色器：21,286 个；着色器转换链 `totk-native-v8-unverified`。
- 已完成：代码改写结果校验、游戏数据和 DLC 校验、静态编译、最低系统版本与 Metal 4 类引用检查、成品深度严格签名校验。
- 未执行：游戏启动、运行时探针、GPU 预热、画面及游玩测试。按用户要求由用户自行测试。

## 使用

自行在 Finder 中打开 App。首次运行需要在这台 Mac 上编译着色器和填充管线缓存，请等待预热完成。构建阶段没有执行 GPU 预热，也没有在空间有限时额外生成离线 metallib。

保存位置（由成品启动器管理）：

- 用户数据：`~/Library/Application Support/MacNativeGames/BotW`
- 运行日志：`~/Library/Logs/MacNativeGames/botw.log`

此构建保留游戏原有抗锯齿及 Metal 3 可用的渲染路径。MetalFX 补帧和上游新增的 Metal 4 时域处理在此构建中关闭，设置面板会显示其不可用。它不会因系统升级自动切换为 Metal 4 后端；未在 macOS 26 上进行成品验证。

## 源码和缓存

- 已适配源码：同目录的 `MacNativeGames-botw-macos15/`。
- 上游固定提交：`984ad05e927c65374f6bf504cdd5803e3b426792`。
- Metal 3 兼容层来源：社区提交 `6948e231b6dfc113b152baab40497db8501d8479`，已适配到新版共享运行时。
- 恢复补丁：同目录的 `botw160-sequoia-adaptation.patch`，用于上述固定上游提交。
- 独立缓存：工作区的 `work/BotW_build/`，含代码、合并数据、DLC、字体和启动着色器。
- 验证记录：同目录的 `BotW-Sequoia-build-validation.json`。

本次对原 `prod.keys` 中的无关格式异常字段采用私有临时派生密钥副本，构建完成后已删除该副本；原文件不变，成品不含密钥。

## 空间与构建参数

本次验证了缓存与成品位于同一 APFS 卷，15GB 镜像可用原生 `clonefile` 共享数据块。构建增加了禁止大型回退复制和保留 4GiB 空间的检查。

再次构建时使用以下环境设置和 `build_app.py --skip-launch-check`；输入路径仍须按实际位置提供：

```sh
TOTK_M3=1 MACOSX_DEPLOYMENT_TARGET=15.0 \
MNG_SKIP_RUNTIME_CHECKS=1 MNG_REQUIRE_CLONE=1 MNG_MIN_FREE_GIB=4 \
MNG_SKIP_OFFLINE_SHADER_LIBS=1 \
python3.14 build_app.py "<原始1.6.0合并XCI>" \
  --keys "<格式已核实的私有临时派生密钥文件>" \
  --shared-fonts "<BotW_build/totk/extracted/firmware/shared-fonts>" \
  --work "<独立BotW_build目录>" \
  -o "<成品路径>.app" --skip-launch-check
```

不要把上次的 TOTK 专用构建入口或补丁用于此游戏。保留本次的独立源码和缓存，可以复用已验证的结果。

## 2026-10-30 花屏修正

用户报告全程花屏。补充 Metal 3 间接纹理与缓冲的逐通道使用声明，通过渲染线程队列按顺序传递，并避开只缓存地址而跳过资源声明的路径；采样器不作为 MTLResource 处理。用户随后确认花屏消失、画面正常，继续由用户测试。旧运行程序保存在工作缓存中，成品路径不变。

排查授权仅用于此次图形问题；非运行检查期间关闭游戏，后续对照应限时运行并保证退出。
