# -*- coding: utf-8 -*-
"""《小林(Xiaolin)》角色复用模块 —— 用于另一台机器上的 Blender 脚本调用。

把 xiaolin_rig.blend 里的角色追加进当前工程，并提供两套用法：
  1) 程序化 K 帧（与 ep01 lib.Character 一致的姿势 API）：walk_cycle / run_cycle / sit ...
  2) 直接套用打包好的动作：apply_action("walk") / apply_action("stretch") ...

用法:
    import sys; sys.path.insert(0, r"此处放 xiaolin_rig 文件夹路径")
    from load_xiaolin import Xiaolin

    lin = Xiaolin(loc=(0, 0, 0), heading_deg=0)   # 追加角色
    lin.walk_cycle(1, 121)                         # 原地走循环 K 帧
    lin.key_root(60, loc=(0, -2, 0))               # root 位移自己控制
    lin.apply_action("sit", start=140)             # 直接套用打包动作
"""
import bpy, os, re, math
from mathutils import Vector

BLEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xiaolin_rig.blend")
COLL = "CHAR_Xiaolin"
HIP_H = 0.90


class Xiaolin:
    """追加 CHAR_Xiaolin 集合并包装成可 K 帧的小人。多实例用不同 name。"""

    def __init__(self, name="Xiaolin", loc=(0, 0, 0), heading_deg=0, scale=1.0):
        with bpy.data.libraries.load(BLEND, link=False) as (src, dst):
            dst.collections = [COLL]
            dst.actions = list(src.actions)   # 同时把打包的动作一起追加进来
        self.coll = bpy.data.collections[COLL]
        self.coll.name = "CHAR_" + name          # 立刻改名，下次追加不会重名复用
        if "CHAR_" + name not in {c.name for c in bpy.context.scene.collection.children}:
            bpy.context.scene.collection.children.link(self.coll)

        self.name = name
        for ob in list(self.coll.objects):
            if ob.name.startswith("Xiaolin"):
                base = re.sub(r"\.\d+$", "", ob.name)  # 去掉追加时的 .001 后缀
                ob.name = name + base[len("Xiaolin"):]
        # 清掉入库前的残留动画，避免与本次 K 帧打架
        for ob in self.coll.objects:
            if ob.animation_data:
                ob.animation_data_clear()

        self.root = bpy.data.objects[name + "_root"]
        self.root.location = loc
        self.root.rotation_euler.z = math.radians(heading_deg)
        self.root.scale = (scale, scale, scale)

        self.J = {}
        for k in ("hips", "spine", "neck"):
            self.J[k] = bpy.data.objects[f"{name}_{k}"]
        for side in ("L", "R"):
            for k in ("sh", "el", "hip", "kn"):
                self.J[f"{k}_{side}"] = bpy.data.objects[f"{name}_{k}_{side}"]
        self.HIP_H = HIP_H

    # ---- 姿势 API（与 ep01 lib.Character 一致）----
    POSE_KEYS = ("spine", "neck", "sh_L", "sh_R", "el_L", "el_R",
                 "hip_L", "hip_R", "kn_L", "kn_R")

    def pose(self, frame=None, hips_dz=0.0, **ang):
        """ang 单位：弧度，绕本地 X 轴。hip/sh 正=向前抬；kn 负=膝弯；
        el 正=肘弯；spine/neck 负=前倾/低头"""
        self.J["hips"].location.z = self.HIP_H + hips_dz
        for k in self.POSE_KEYS:
            self.J[k].rotation_euler.x = ang.get(k, 0.0)
        if frame is not None:
            self.J["hips"].keyframe_insert("location", frame=frame)
            for k in self.POSE_KEYS:
                self.J[k].keyframe_insert("rotation_euler", frame=frame)

    def key_root(self, frame, loc=None, heading_deg=None):
        if loc is not None:
            self.root.location = loc
            self.root.keyframe_insert("location", frame=frame)
        if heading_deg is not None:
            self.root.rotation_euler.z = math.radians(heading_deg)
            self.root.keyframe_insert("rotation_euler", frame=frame)

    def stand(self, frame=None, head=0.0, breathe=0.0):
        self.pose(frame, hips_dz=breathe, neck=head, sh_L=0.05, sh_R=0.05, el_L=0.12, el_R=0.12)

    def sit(self, frame=None, head=-0.15):
        self.pose(frame, hips_dz=-0.78, spine=-0.3, neck=head,
                  hip_L=2.4, hip_R=2.4, kn_L=-1.9, kn_R=-1.9, sh_L=1.25, sh_R=1.25, el_L=0.7, el_R=0.7)

    def head_in_hands(self, frame=None):
        self.pose(frame, spine=-0.25, neck=-0.55, sh_L=2.35, sh_R=2.35, el_L=2.0, el_R=2.0)

    def slump(self, frame=None):
        self.pose(frame, hips_dz=-0.02, spine=-0.35, neck=-0.6, sh_L=-0.05, sh_R=-0.05, el_L=0.05, el_R=0.05)

    def look_up(self, frame=None):
        self.pose(frame, spine=0.12, neck=0.55, sh_L=0.1, sh_R=0.1, el_L=0.2, el_R=0.2)

    def crouch(self, frame=None):
        self.pose(frame, hips_dz=-0.42, spine=-0.5, neck=-0.3,
                  hip_L=1.6, hip_R=1.6, kn_L=-2.4, kn_R=-2.4, sh_L=1.4, sh_R=1.4, el_L=1.3, el_R=1.3)

    def reach(self, frame=None):
        self.pose(frame, spine=-0.08, neck=0.05, sh_L=1.5, sh_R=0.1, el_L=0.1, el_R=0.2)

    # ---- 循环动作（原地，root 位移自己控制）----
    def _cycle(self, f0, f1, A, B, C, bob, lean, elb, head=0.0):
        F = f1 - f0
        for i in range(F + 1):
            f = f0 + i
            ph = 2 * math.pi * i / F
            s, c = math.sin(ph), math.cos(ph)
            self.pose(f, hips_dz=-bob * 0.5 + bob * abs(c), spine=lean, neck=head,
                      hip_L=A * s, hip_R=-A * s,
                      kn_L=-B * max(0.0, c) - 0.08, kn_R=-B * max(0.0, -c) - 0.08,
                      sh_L=-C * s, sh_R=C * s, el_L=elb, el_R=elb)
        self.stand(f1 + 6, head=head)

    def walk_cycle(self, f0, f1, head=0.0):
        """原地走循环（48帧一步循环；f1-f0 为 48 的整数倍最顺）"""
        self._cycle(f0, f1, 0.42, 0.75, 0.40, 0.03, -0.04, 0.25, head)

    def run_cycle(self, f0, f1, head=0.0):
        """原地跑循环（32帧一步循环；f1-f0 为 32 的整数倍最顺）"""
        self._cycle(f0, f1, 0.85, 1.50, 0.95, 0.06, -0.28, 1.30, head + 0.10)

    def breathe(self, f0, f1):
        """待机呼吸循环（48帧周期；f1-f0 为 48 的整数倍最顺）"""
        F = f1 - f0
        for i in range(F + 1):
            f = f0 + i
            ph = 2 * math.pi * i / 48
            self.pose(f, hips_dz=0.015 * math.sin(ph), spine=0.02 * math.sin(ph + 0.7),
                      neck=0.04 * math.sin(ph + 1.6) - 0.02,
                      sh_L=0.05 + 0.02 * math.sin(ph + 0.5), sh_R=0.05 + 0.02 * math.sin(ph + 0.5),
                      el_L=0.12, el_R=0.12)

    def stretch_cycle(self, f0, f1):
        """伸展/伸懒腰循环（24帧周期；f1-f0 为 24 的整数倍最顺）"""
        F = f1 - f0
        for i in range(F + 1):
            f = f0 + i
            ph = 2 * math.pi * i / 24
            s = math.sin(ph)
            self.pose(f, hips_dz=0.01 * s, spine=0.05 + 0.03 * s, neck=0.12,
                      hip_L=0.05 + 0.05 * s, hip_R=-0.05 - 0.05 * s, kn_L=-0.12, kn_R=-0.12,
                      sh_L=2.75 + 0.06 * s, sh_R=2.75 - 0.06 * s, el_L=0.03, el_R=0.03)

    # ---- 沿路径走/跑（root 带位移，与 ep01 locomote 相同）----
    def locomote(self, f0, f1, path, run=False, step=None, head=0.0):
        """path(u)->(x,y)，u∈[0,1]。自动朝向切线。"""
        step = step or (1.35 if run else 0.62)
        A, B, C, bob, lean = (0.85, 1.5, 0.95, 0.06, -0.28) if run else (0.42, 0.75, 0.4, 0.03, -0.04)
        pts = [Vector((*path(i / 200), 0)) for i in range(201)]
        L = sum((pts[i + 1] - pts[i]).length for i in range(200))
        cum = [0.0]
        for i in range(200):
            cum.append(cum[-1] + (pts[i + 1] - pts[i]).length)
        for f in range(f0, f1 + 1):
            u_t = (f - f0) / max(1, (f1 - f0))
            d = u_t * L
            j = min(199, max(0, next((i for i in range(200) if cum[i + 1] >= d), 199)))
            seg = (d - cum[j]) / max(1e-6, cum[j + 1] - cum[j])
            p = pts[j].lerp(pts[j + 1], seg)
            tan = (pts[j + 1] - pts[j]).normalized()
            hd = math.degrees(math.atan2(-tan.x, tan.y))
            ph = d / step * math.pi
            s = math.sin(ph)
            self.root.location = (p.x, p.y, self.root.location.z)
            self.root.rotation_euler.z = math.radians(hd)
            self.root.keyframe_insert("location", frame=f)
            self.root.keyframe_insert("rotation_euler", frame=f)
            elb = 1.3 if run else 0.25
            self.pose(f, hips_dz=-bob * 0.5 + bob * abs(math.cos(ph)), spine=lean, neck=head + (0.1 if run else 0),
                      hip_L=A * s, hip_R=-A * s,
                      kn_L=-B * max(0.0, math.cos(ph)) - 0.08, kn_R=-B * max(0.0, -math.cos(ph)) - 0.08,
                      sh_L=-C * s, sh_R=C * s, el_L=elb, el_R=elb)
        self.stand(f1 + 6, head=head)
        return L

    # ---- 直接套用打包好的 Action ----
    def apply_action(self, name, start=1):
        """把 xiaolin_rig.blend 里打包的动作(独立 Action)套用到当前角色。
        返回该动作的帧范围 (首帧, 末帧)。循环动作套用后即从 start 帧起播。"""
        ac = bpy.data.actions.get(name)
        if ac is None:
            raise KeyError(f"动作 '{name}' 不存在，可用: {[a.name for a in bpy.data.actions if a.use_fake_user]}")
        targets = [self.root] + list(self.J.values())
        for ob in targets:
            ad = ob.animation_data_create()
            slot = next((s for s in ac.slots if s.identifier == "OB" + ob.name), None)
            if slot:
                ad.action = ac
                ad.action_slot = slot
            else:
                ad.action = ac  # 退路：直接挂动作（部分 Blender 版本无 slot 概念）
        return tuple(ac.frame_range)
