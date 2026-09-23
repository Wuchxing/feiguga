# 肥咕嘎桌面宠物

一个基于 Python + PyQt5 的 Windows 桌面宠物。支持透明置顶窗口、角色区域点击、拖拽弹性跟随、呼吸动画、淡入淡出、托盘、表情菜单、闲置状态及开机自启。

全部 14 个状态均包含 60 帧角色动画，以 30 FPS 播放。运行时只缓存当前状态的动画帧，内存设计目标不超过 200 MB。

## 运行

需要 Windows 10/11 和 Python 3.9+（安装 Python 时勾选 `py launcher`）。双击 `run.bat`，首次运行会自动创建虚拟环境、安装依赖并处理素材。也可以手动执行：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe process_assets.py
.\.venv\Scripts\python.exe main.py
```

操作：点击腹部喂食，点击嘴部触发捂嘴，点击额头触发生气，双击打滚。拖动时会根据方向和速度切换慢跑、快跑、跳跃或向下爬梯动作；悬停 2 秒招手，右键打开表情与设置菜单。关闭/隐藏后可从系统托盘恢复。

情绪和移动均使用角色自身姿势表现，不通过整幅画面抖动或旋转模拟。哭泣状态会双手捂眼、泪珠滑落并呈方形下撇哭嘴；向下爬梯使用角色背面视角。

连续静止 5 分钟后，宠物会在屏幕底部自动慢跑；任何点击或拖动都会停止自动移动。也可以在右键菜单选择“喂食”。

## 替换素材

将新 PNG 放进 `assets/` 并保持原文件名，然后删除 `assets_processed/`，重新运行 `process_assets.py`。处理器适用于边缘连通的浅灰/白色背景；若素材已带透明通道，可直接按同名复制到 `assets_processed/`。建议原图为正方形且角色居中。

## 打包 EXE

双击 `build.bat`。完成后程序位于 `dist/FeigugaPet/FeigugaPet.exe`。目录模式可避免单文件包每次启动解压素材，启动更快、内存占用也更稳定。

## 项目结构

- `main.py`：窗口、鼠标交互、动画、托盘及系统集成
- `state_machine.py`：状态定义与闲置状态机
- `asset_manager.py`：按需加载和缩放素材
- `settings_dialog.py`：大小、透明度和开机自启设置
- `process_assets.py`：素材透明化预处理
- `generate_animations.py`：从角色关键姿势生成每状态 60 帧动画
