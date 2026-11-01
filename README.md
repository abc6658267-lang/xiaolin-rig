# 小林 (Xiaolin) — 可复用 3D 角色资产

一个程序化生成的低多边形 3D 角色「小林」，用于 Blender 脚本化动画短片（风格与《职场自我内耗》EP01 统一）。

- **模型**：低多边形小人（芥末黄开衫、白衬衫、灰裤、白鞋）
- **骨骼**：12 关节空物体骨架（root / hips / spine / neck + 双臂双腿关节）
- **动作**：11 个内置 Action —— `idle` `walk` `run` `sit` `get_up` `slump` `head_in_hands` `look_up` `crouch` `reach` `stretch`
- **材质**：已 `打包资源`（贴图内嵌进 .blend，无需外部文件）

## 文件说明

| 文件 | 说明 |
|---|---|
| `xiaolin_rig.blend` | 角色资产：模型 + 骨骼 + 11 个动作（以静止姿势入库，动作随文件携带） |
| `actions.txt` | 每个动作的名字 / 帧数 / 说明 |
| `load_xiaolin.py` | 另一台机器脚本调用助手（见下） |

> 打包好的 `xiaolin_rig.zip`（含上述三个文件）放在 **[Releases](../../releases)** 里，可直接下载。

## 在另一台电脑的 Blender 脚本里调用

```python
import sys
sys.path.insert(0, r"路径/xiaolin_rig")   # 放 load_xiaolin.py 的目录
from load_xiaolin import Xiaolin

lin = Xiaolin(loc=(0, 0, 0))        # 实例化，可选 heading_deg / scale
lin.walk_cycle(1, 121)              # 程序化 K 帧：走路循环
lin.run_cycle(1, 81)                # 跑步循环
lin.apply_action("stretch")          # 或直套打包动作库里的某个 Action
lin.key_root(30, loc=(0, -1, 0), heading_deg=90)   # 手动 K 根骨骼位移/朝向
```

`walk/run` 是原地循环（四肢动、位置不动），可配任意路径；`sit/slump/head_in_hands/look_up/crouch/reach` 是静态姿势；`get_up/stretch` 是过渡/循环动作。

## 许可

可自由用于个人 / 非商业动画项目。
