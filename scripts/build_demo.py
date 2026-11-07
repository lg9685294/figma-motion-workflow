"""Rebuild the original, anonymous documentation illustrations.

Optional maintenance dependency: Pillow >= 10 (not needed to use the Skill or
the standard-library timeline tool). Run from any directory:

    python3 scripts/build_demo.py --font /path/to/a/CJK-font.ttf

A system CJK font is selected when --font is omitted. The existing assets are
ready to read; rebuilding is optional. Pass the same font and Pillow version
for matching raster typography. No network access or Figma/project media is
used. The GIF is a code illustration, never a measured Figma export.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
SKILL = ROOT / "skills/figma-motion-workflow"
ASSETS.mkdir(parents=True, exist_ok=True)

spec = json.loads((SKILL / "assets/timeline.example.json").read_text())
module_spec = importlib.util.spec_from_file_location("motion_timeline", SKILL / "scripts/timeline.py")
timeline = importlib.util.module_from_spec(module_spec)
import sys
sys.modules[module_spec.name] = timeline
module_spec.loader.exec_module(timeline)
audit = timeline.audit(spec)
assert audit["complete"] and audit["resolution_complete"], audit
events = {item["id"]: item for item in audit["events"]}

workflow = '''<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="420" viewBox="0 0 1120 420" role="img" aria-labelledby="title desc">
<title id="title">从参考材料到动效验收的工作流</title>
<desc id="desc">确认材料与能力，锁定几何与需求，建立事件依赖，按能力实现，实际播放与逐帧验收。各阶段输出可追踪证据；未知项保留待核验。</desc>
<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0 7 3.5 0 7" fill="none" stroke="#8c959f" stroke-width="1.2"/></marker></defs>
<rect width="1120" height="420" rx="12" fill="#f6f8fa"/>
<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,PingFang SC,Microsoft YaHei,sans-serif">
<text x="40" y="49" font-size="22" font-weight="600" fill="#1f2328">把动效需求变成可追踪的制作与验收</text>
<text x="40" y="78" font-size="14" fill="#59636e">每一步都有明确产物；没有源数据的项目保留待核验。</text>
__BOXES__
<path d="M986 253 V302 H142 V262" fill="none" stroke="#8c959f" stroke-width="1.5" stroke-dasharray="5 5" marker-end="url(#arrow)"/>
<rect x="411" y="288" width="300" height="27" rx="13" fill="#f6f8fa"/>
<text x="561" y="307" text-anchor="middle" font-size="13" fill="#59636e">发现差异 → 只修相关属性与下游依赖</text>
<path d="M40 341 H1080" stroke="#d1d9e0"/>
<text x="40" y="373" font-size="13" fill="#59636e">原创工作流图示 · 不含客户素材、私有节点或项目参数</text>
<text x="40" y="397" font-size="12" fill="#59636e">代码预览与 Figma 源时间轴、实际播放、交互重放分别验收。</text>
</g></svg>'''
steps = [
    ("01", "收拢材料与能力", "源文件 / 版本 / 可读写范围", "产物：来源索引"),
    ("02", "锁定几何与需求", "形状 / 起点 / 有效修改", "产物：生效规格"),
    ("03", "建立事件依赖", "属性阈值 / 曲线 / 总时长", "产物：时间审计"),
    ("04", "按可用能力实现", "分层 / 原型 / 制作提示词", "产物：可交接实现"),
    ("05", "播放与逐帧验收", "首帧 / 阈值 / 末帧 / 重放", "产物：验收记录"),
]
boxes = []
for index, (number, title, line, output) in enumerate(steps):
    x = 40 + index * 210
    boxes.append(f'<rect x="{x}" y="115" width="198" height="138" rx="7" fill="white" stroke="#d1d9e0"/><text x="{x+15}" y="144" font-size="13" font-weight="600" fill="#0969da">{number}</text><text x="{x+15}" y="173" font-size="17" font-weight="600" fill="#1f2328">{title}</text><text x="{x+15}" y="199" font-size="12" fill="#59636e">{line}</text><text x="{x+15}" y="230" font-size="13" fill="#1f2328">{output}</text>')
    if index < len(steps) - 1:
        boxes.append(f'<path d="M{x+199} 184 H{x+209}" stroke="#8c959f" stroke-width="1.5" marker-end="url(#arrow)"/>')
(ASSETS / "workflow.svg").write_text(workflow.replace("__BOXES__", "".join(boxes)))

# The curve, star and layout below are new anonymous geometry for this diagram.
SCALE = 2
WIDTH, HEIGHT = 960, 550
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--font", type=Path, help="Path to a CJK font (.ttf/.otf/.ttc)")
args = parser.parse_args()
font_candidates = ([args.font] if args.font else []) + [
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("C:/Windows/Fonts/msyh.ttc"),
]
font_path = next((p for p in font_candidates if p and p.is_file()), None)
if font_path is None:
    raise SystemExit("A CJK font is needed. Pass --font /path/to/font.ttf to rebuild the GIF.")
def font(size):
    return ImageFont.truetype(str(font_path), size * SCALE)
fonts = {s: font(s) for s in (12, 13, 14, 15, 16, 17, 20, 24)}
def draw_text(draw, xy, message, size=14, fill="#1f2328"):
    draw.text((xy[0]*SCALE, xy[1]*SCALE), message, font=fonts[size], fill=fill)
def line(draw, points, fill="#0969da", width=5):
    draw.line([(x*SCALE,y*SCALE) for x,y in points], fill=fill, width=width*SCALE, joint="curve")
def rect(draw, xy, fill, outline=None, radius=5):
    draw.rounded_rectangle(tuple(v*SCALE for v in xy), radius*SCALE, fill=fill, outline=outline, width=SCALE)

path = []
for i in range(401):
    u = i/400
    # A smooth, newly drawn route ending under the star.
    x = (1-u)**3*134 + 3*(1-u)**2*u*325 + 3*(1-u)*u*u*548 + u**3*806
    y = (1-u)**3*235 + 3*(1-u)**2*u*80 + 3*(1-u)*u*u*286 + u**3*177
    path.append((x,y))
lengths = [0]
for p, q in zip(path, path[1:]):
    lengths.append(lengths[-1]+math.dist(p,q))
def reveal(progress):
    target = max(0, min(1, progress))*lengths[-1]
    output = [path[0]]
    for i in range(1,len(path)):
        if lengths[i] >= target:
            frac = (target-lengths[i-1])/(lengths[i]-lengths[i-1])
            output.append(tuple(path[i-1][j]+frac*(path[i][j]-path[i-1][j]) for j in (0,1)))
            break
        output.append(path[i])
    return output
def bezier_progress(u):
    # x(t)=(0,0,.58,1); y(t)=(0,0,1,1). Find parameter at wall-clock u.
    lo, hi = 0., 1.
    for _ in range(45):
        t = (lo+hi)/2
        x = 3*(1-t)*t*t*.58+t*t*t
        if x < u: lo=t
        else: hi=t
    t = (lo+hi)/2
    return 3*(1-t)*t*t+t*t*t
def progress_at(t, event, easing=False):
    p = min(1,max(0,(t-events[event]["start_ms"])/events[event]["duration_ms"]))
    return bezier_progress(p) if easing else p
def star(draw, center, radius, angle, opacity):
    layer = Image.new("RGBA", (WIDTH*SCALE,HEIGHT*SCALE))
    pen = ImageDraw.Draw(layer)
    points=[]
    for i in range(10):
        a = angle + math.radians(-90+i*36)
        r = radius if i%2==0 else radius*.45
        points.append(((center[0]+r*math.cos(a))*SCALE,(center[1]+r*math.sin(a))*SCALE))
    pen.polygon(points,fill=(191,135,0,round(255*opacity)))
    return layer

frames=[]
times = list(range(0,761,20))
for t in times:
    image=Image.new("RGB",(WIDTH*SCALE,HEIGHT*SCALE),"white")
    d=ImageDraw.Draw(image)
    draw_text(d,(32,22),"Timing demo",24)
    draw_text(d,(32,59),"匿名代码示意 · 非 Figma 实测导出 · 演示值，不是通用参数",14,"#59636e")
    rect(d,(32,99,928,293),"#f6f8fa","#d1d9e0",8)
    line(d,path,"#d1d9e0",4)
    p=progress_at(t,"line",True)
    active=reveal(p)
    if p>0: line(d,active,"#0969da",5)
    x,y=active[-1]
    d.ellipse(((x-4)*SCALE,(y-4)*SCALE,(x+4)*SCALE,(y+4)*SCALE),fill="#0969da")
    if t >= events["appear"]["start_ms"]:
        appearance=progress_at(t,"appear")
        image=image.convert("RGBA")
        image=Image.alpha_composite(image,star(d,(806,148),26*(.6+.4*appearance),math.radians(90*progress_at(t,"rotate")),appearance))
        image=image.convert("RGB"); d=ImageDraw.Draw(image)
    draw_text(d,(49,112),f"path {p*100:.0f}%",14,"#0969da")
    draw_text(d,(767,259),f"t = {min(t,audit['resolved_total_ms']):.0f} ms",14,"#59636e")
    if t < events["line"]["start_ms"]:
        status="等待 line 开始"
    elif t < events["appear"]["start_ms"]:
        status="line 生长；按属性进度判断阈值"
    elif t < events["rotate"]["start_ms"]:
        status="line 达到 90% → 小星开始显现"
    elif t < events["settle"]["start_ms"]:
        status="显现达到 90% → 小星开始旋转"
    else:
        status="旋转结束 → 保留 50 ms 稳定段"
    draw_text(d,(32,309),status,17)
    track_left,track_right=150,908
    total=800
    for row,(event,label,color) in enumerate([("line","LINE","#0969da"),("appear","APPEAR","#bf8700"),("rotate","ROTATE","#8250df")]):
        y=354+row*36
        draw_text(d,(33,y-6),label,13,"#59636e")
        rect(d,(track_left,y,track_right,y+10),"#eaeef2",radius=4)
        e=events[event]
        a=track_left+(track_right-track_left)*e["start_ms"]/total
        b=track_left+(track_right-track_left)*e["end_ms"]/total
        rect(d,(a,y,b,y+10),color,radius=4)
        cursor=track_left+(track_right-track_left)*min(t,audit["resolved_total_ms"])/total
        line(d,[(cursor,y-5),(cursor,y+15)],"#1f2328",1)
    draw_text(d,(32,471),f"line 100–400 ms  ·  appear {events['appear']['start_ms']:.1f} ms  ·  rotate {events['rotate']['start_ms']:.1f} ms",13,"#59636e")
    draw_text(d,(32,496),"E(u)=cubic-bezier(0,0,0.58,1)  ·  源时间按 1× 播放；末帧停留后循环",13,"#59636e")
    draw_text(d,(32,520),"时间来自仓库 timeline.example.json 与 timeline.py audit；不验证 Figma 或源几何。",12,"#59636e")
    frames.append(image.resize((WIDTH,HEIGHT),Image.Resampling.LANCZOS).quantize(colors=128,method=Image.Quantize.MEDIANCUT))
durations=[20]*len(frames)
durations[0]=220
durations[-1]=1300
frames[0].save(ASSETS/"timing-demo.gif",save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=True,disposal=2)
(ASSETS/"timing-demo-audit.json").write_text(json.dumps({"status":"anonymous-code-illustration-not-figma-export","spec_source":"../../skills/figma-motion-workflow/assets/timeline.example.json","audit":audit},ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"assets":["workflow.svg","timing-demo.gif","timing-demo-audit.json"],"total_ms":audit["resolved_total_ms"]},ensure_ascii=False))
