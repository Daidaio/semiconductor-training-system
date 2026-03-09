# -*- coding: utf-8 -*-
"""
Virtual Fab 第一人稱 3D 互動介面
- Three.js 渲染 ASML GLB 模型
- Raycasting 點擊 mesh → 觸發操作
- postMessage 雙向通訊
- AI 學長整合
"""

import gradio as gr
import types
import threading
import functools
import http.server
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from interface.simulation_interface import SimulationTrainingSystem

# ── 資源路徑 ────────────────────────────────────────────────────────────────
_STATIC = Path(__file__).parent.parent / "static"
_GLB_PATH = _STATIC / "asml_duv.glb"

# ── 本地 CORS HTTP 伺服器（讓 Three.js iframe 直接用 URL 載入 GLB）─────────
_glb_server_port: int = 0

class _CORSHandler(http.server.SimpleHTTPRequestHandler):
    """加上 CORS 標頭的靜態檔案伺服器"""
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=86400")
        super().end_headers()
    def log_message(self, *a):
        pass  # 不輸出 access log

def _start_glb_server(directory: str, port: int = 8765) -> int:
    """啟動背景 HTTP 伺服器，回傳實際使用的 port"""
    global _glb_server_port
    if _glb_server_port:
        return _glb_server_port
    handler = functools.partial(_CORSHandler, directory=directory)
    for p in range(port, port + 20):
        try:
            server = http.server.HTTPServer(("127.0.0.1", p), handler)
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            _glb_server_port = p
            print(f"[OK] GLB 伺服器: http://127.0.0.1:{p}/")
            return p
        except OSError:
            continue
    raise RuntimeError("找不到可用的 port 啟動 GLB 伺服器")

# ── 微型透明 GIF（用 onload 執行 JS）──────────────────────────────────────
_GIF = "data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="

_CSS = """
body,.gradio-container{background:#050d1a!important;}
.hmi-btn button{font-size:12px!important;min-height:40px!important;
  font-family:Consolas,monospace!important;width:100%!important;border-radius:6px!important;}
.hmi-btn-stop button{background:#1a0505!important;border:1px solid #7a0000!important;color:#ff5555!important;}
#fp_input textarea{background:#0a1220!important;border:1px solid #2a4a6b!important;
  color:#a0d0ff!important;font-family:Consolas,monospace!important;}
"""

_PLACEHOLDER = """<div style="height:580px;background:linear-gradient(135deg,#050d1a,#0a1528);
  border:2px solid #1a3a5c;border-radius:12px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;color:#4af;gap:16px;">
  <div style="font-size:64px;opacity:0.25;">⚙</div>
  <div style="font-size:15px;letter-spacing:3px;opacity:0.7;">ASML TWINSCAN NXT:870</div>
  <div style="font-size:12px;color:#5a8a9a;">按「▶ 開始新情境」啟動設備</div>
</div>"""

_DASH_PLACEHOLDER = ('<div style="background:linear-gradient(90deg,#0a1220,#0d1b2a);'
                     'border:1px solid #1a3a5c;border-radius:8px;padding:8px 14px;'
                     'color:#6ab;font-size:12px;font-family:Consolas,monospace;">'
                     '⏳ 等待情境開始…</div>')


# ══════════════════════════════════════════════════════════════════════════════
# Three.js 互動式 3D 檢視器
# 策略：將 viewer.html 寫入 static/ 並透過本地 HTTP server 以 src= 載入，
# 避免 srcdoc null-origin + ES module 在沙箱 iframe 中的不相容問題。
# ══════════════════════════════════════════════════════════════════════════════

_VIEWER_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#050d1a;overflow:hidden;width:100vw;height:100vh;}
#tip{position:fixed;display:none;background:rgba(0,6,18,.92);
     color:#ffa500;padding:6px 14px;border-radius:6px;
     font:12px Consolas,monospace;border:1px solid rgba(255,165,0,.33);
     pointer-events:none;z-index:99;white-space:nowrap;}
#hud{position:fixed;top:10px;left:10px;
     background:rgba(0,6,18,.8);color:#4af;
     padding:6px 12px;border-radius:6px;
     font:11px Consolas,monospace;border:1px solid #2a5a9c;
     pointer-events:none;letter-spacing:.5px;}
#loading{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
         color:#4af;font:14px Consolas,monospace;text-align:center;}
#pct{margin-top:8px;font-size:22px;color:#ffa500;}
#xhair{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
       width:22px;height:22px;pointer-events:none;opacity:0.5;}
#xhair::before,#xhair::after{content:'';position:absolute;background:#ffa500;}
#xhair::before{width:2px;height:100%;left:50%;transform:translateX(-50%);}
#xhair::after{width:100%;height:2px;top:50%;transform:translateY(-50%);}
</style>
</head>
<body>
<div id="loading">
  \u23f3 \u8f09\u5165 3D \u6a21\u578b\u4e2d\u2026
  <div id="pct">0%</div>
  <small style="color:#5a8a9a;margin-top:8px;display:block;">\u79fb\u52d5\u6ed1\u9f20\u65cb\u8f49 | \u6efe\u8f2a\u7e2e\u653e | \u9ede\u64ca\u90e8\u4ef6\u6aa2\u67e5</small>
</div>
<div id="tip"></div>
<div id="hud">\ud83d\udc41 \u9ede\u64ca\u8a2d\u5099\u90e8\u4ef6\u9032\u884c\u6aa2\u67e5</div>
<div id="xhair"></div>

<!-- Three.js r128 global build (non-module) — most reliable in iframe context -->
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
var MA = {
  Stage_Base:'\u67e5\u770b\u6676\u5713\u8f09\u53f0\u4f4d\u7f6e\u8aa4\u5dee',
  'Rail_-0.6':'\u67e5\u770b\u6676\u5713\u8f09\u53f0\u4f4d\u7f6e\u8aa4\u5dee',
  'Rail_0.0':'\u67e5\u770b\u6676\u5713\u8f09\u53f0\u4f4d\u7f6e\u8aa4\u5dee',
  'Rail_0.6':'\u67e5\u770b\u6676\u5713\u8f09\u53f0\u4f4d\u7f6e\u8aa4\u5dee',
  Wafer_Chuck:'\u67e5\u770b\u6676\u5713\u8f09\u53f0\u4f4d\u7f6e\u8aa4\u5dee',
  Wafer:'\u67e5\u770b\u6676\u5713\u8f09\u53f0\u4f4d\u7f6e\u8aa4\u5dee',
  Label_Stage:'\u67e5\u770b\u6676\u5713\u8f09\u53f0\u4f4d\u7f6e\u8aa4\u5dee',
  POB_Barrel:'\u6aa2\u67e5\u6295\u5f71\u93e1\u7d44\u6eab\u5ea6',
  POB_Top_Cap:'\u6aa2\u67e5\u6295\u5f71\u93e1\u7d44\u6eab\u5ea6',
  POB_Bottom:'\u6aa2\u67e5\u6295\u5f71\u93e1\u7d44\u6eab\u5ea6',
  Label_POB:'\u6aa2\u67e5\u6295\u5f71\u93e1\u7d44\u6eab\u5ea6',
  Illum_Barrel:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Label_Illum:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Laser_Box:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Laser_Vent:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Laser_Out:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Label_Laser:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Beam_H1:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Beam_V1:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Beam_H2:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Beam_V2:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Beam_Spot:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Mirror1:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Mirror2:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Mirror3:'\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027',
  Immersion_Hood:'\u6aa2\u67e5\u51b7\u537b\u6c34\u6d41\u91cf\u548c\u6eab\u5ea6',
  Immersion_Supply:'\u6aa2\u67e5\u51b7\u537b\u6c34\u6d41\u91cf\u548c\u6eab\u5ea6',
  Immersion_Return:'\u6aa2\u67e5\u51b7\u537b\u6c34\u6d41\u91cf\u548c\u6eab\u5ea6',
  Label_Immersion:'\u6aa2\u67e5\u51b7\u537b\u6c34\u6d41\u91cf\u548c\u6eab\u5ea6',
  Duct_Top:'\u6aa2\u67e5\u771f\u7a7a\u7cfb\u7d71\u58d3\u529b',
  Duct_Vent1:'\u6aa2\u67e5\u771f\u7a7a\u7cfb\u7d71\u58d3\u529b',
  Duct_Vent2:'\u6aa2\u67e5\u771f\u7a7a\u7cfb\u7d71\u58d3\u529b',
  Cabinet_Main:'\u67e5\u770b\u63a7\u5236\u7cfb\u7d71\u72c0\u614b',
  Cabinet_Panel:'\u67e5\u770b\u63a7\u5236\u7cfb\u7d71\u72c0\u614b',
  Screen:'\u67e5\u770b\u63a7\u5236\u7cfb\u7d71\u72c0\u614b',
  Keyboard:'\u67e5\u770b\u63a7\u5236\u7cfb\u7d71\u72c0\u614b',
  FOUP_Port:'\u78ba\u8a8d\u6676\u5713\u50b3\u9001\u72c0\u614b',
  FOUP_Door:'\u78ba\u8a8d\u6676\u5713\u50b3\u9001\u72c0\u614b',
  Label_FOUP:'\u78ba\u8a8d\u6676\u5713\u50b3\u9001\u72c0\u614b'
};
var ML = {
  Stage_Base:'\u6676\u5713\u8f09\u53f0','Rail_-0.6':'\u6676\u5713\u8f09\u53f0',
  'Rail_0.0':'\u6676\u5713\u8f09\u53f0','Rail_0.6':'\u6676\u5713\u8f09\u53f0',
  Wafer_Chuck:'\u6676\u5713\u8f09\u53f0',Wafer:'\u6676\u5713\u8f09\u53f0',
  Label_Stage:'\u6676\u5713\u8f09\u53f0',
  POB_Barrel:'\u6295\u5f71\u93e1\u7d44',POB_Top_Cap:'\u6295\u5f71\u93e1\u7d44',
  POB_Bottom:'\u6295\u5f71\u93e1\u7d44',Label_POB:'\u6295\u5f71\u93e1\u7d44',
  Illum_Barrel:'\u7167\u660e\u7cfb\u7d71',Label_Illum:'\u7167\u660e\u7cfb\u7d71',
  Laser_Box:'\u96f7\u5c04\u5149\u6e90',Laser_Vent:'\u96f7\u5c04\u5149\u6e90',
  Laser_Out:'\u96f7\u5c04\u5149\u6e90',Label_Laser:'\u96f7\u5c04\u5149\u6e90',
  Beam_H1:'DUV\u5149\u675f',Beam_V1:'DUV\u5149\u675f',
  Beam_H2:'DUV\u5149\u675f',Beam_V2:'DUV\u5149\u675f',Beam_Spot:'DUV\u5149\u675f',
  Mirror1:'\u53cd\u5c04\u93e1',Mirror2:'\u53cd\u5c04\u93e1',Mirror3:'\u53cd\u5c04\u93e1',
  Immersion_Hood:'\u6db2\u6d78\u51b7\u537b',Immersion_Supply:'\u6db2\u6d78\u51b7\u537b',
  Immersion_Return:'\u6db2\u6d78\u51b7\u537b',Label_Immersion:'\u6db2\u6d78\u51b7\u537b',
  Duct_Top:'\u901a\u98a8\u6392\u6c23',Duct_Vent1:'\u901a\u98a8\u6392\u6c23',
  Duct_Vent2:'\u901a\u98a8\u6392\u6c23',
  Cabinet_Main:'\u63a7\u5236\u7cfb\u7d71',Cabinet_Panel:'\u63a7\u5236\u7cfb\u7d71',
  Screen:'\u63a7\u5236\u7cfb\u7d71',Keyboard:'\u63a7\u5236\u7cfb\u7d71',
  FOUP_Port:'\u6676\u5713\u50b3\u9001',FOUP_Door:'\u6676\u5713\u50b3\u9001',
  Label_FOUP:'\u6676\u5713\u50b3\u9001'
};
(function(){
  for(var i=0;i<10;i++){MA['Lens_'+i]='\u6aa2\u67e5\u6295\u5f71\u93e1\u7d44\u6eab\u5ea6';ML['Lens_'+i]='\u6295\u5f71\u93e1\u7d44';}
  for(var i=0;i<6;i++){MA['IllumLens_'+i]='\u67e5\u770b\u5149\u6e90\u5f37\u5ea6\u548c\u7a69\u5b9a\u6027';ML['IllumLens_'+i]='\u7167\u660e\u7cfb\u7d71';}
})();

// ── Scene ──
var scene = new THREE.Scene();
scene.background = new THREE.Color(0x050d1a);

var renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
renderer.setSize(window.innerWidth,window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

var camera = new THREE.PerspectiveCamera(55,window.innerWidth/window.innerHeight,0.01,200);
camera.position.set(0,1.2,6);

// ── Lights ──
scene.add(new THREE.AmbientLight(0xffffff,0.7));
var sun = new THREE.DirectionalLight(0xffffff,1.4);
sun.position.set(6,10,6); sun.castShadow=true;
scene.add(sun);
var fill = new THREE.DirectionalLight(0x4488ff,0.35);
fill.position.set(-6,3,-6); scene.add(fill);
var rim = new THREE.DirectionalLight(0xffeedd,0.2);
rim.position.set(0,-3,-8); scene.add(rim);

// ── Controls ──
var controls = new THREE.OrbitControls(camera,renderer.domElement);
controls.enableDamping=true; controls.dampingFactor=0.06;
controls.minDistance=0.5; controls.maxDistance=20;

// ── Load GLB from same origin ──
var loader = new THREE.GLTFLoader();
loader.load('./asml_duv.glb',
  function(gltf){
    var loadEl=document.getElementById('loading');
    if(loadEl) loadEl.remove();
    var model=gltf.scene;
    model.traverse(function(o){
      if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}
    });
    scene.add(model);
    var box=new THREE.Box3().setFromObject(model);
    var center=box.getCenter(new THREE.Vector3());
    var size=box.getSize(new THREE.Vector3());
    var maxDim=Math.max(size.x,size.y,size.z);
    controls.target.copy(center);
    camera.position.set(center.x,center.y+size.y*0.15,center.z+maxDim*1.6);
    controls.update();
  },
  function(xhr){
    if(xhr.total>0){
      var pct=Math.round(xhr.loaded/xhr.total*100);
      var el=document.getElementById('pct');
      if(el) el.textContent=pct+'%';
    }
  },
  function(err){
    var el=document.getElementById('loading');
    if(el) el.innerHTML='<span style="color:#f44">\u274c \u6a21\u578b\u8f09\u5165\u5931\u6557</span><br><small style="color:#888">'+err+'</small>';
    console.error('GLB error:',err);
  }
);

// ── Raycasting ──
var raycaster=new THREE.Raycaster();
var mouse=new THREE.Vector2(-9,-9);
var hoveredMesh=null;
var origMats=new Map();
var hlMat=new THREE.MeshStandardMaterial({color:0xffa500,emissive:0x331100,metalness:0.3,roughness:0.4});

function getAction(obj){
  var o=obj;
  while(o){if(MA[o.name])return[ML[o.name]||o.name,MA[o.name]];o=o.parent;}
  return null;
}

var tip=document.getElementById('tip');

window.addEventListener('mousemove',function(e){
  mouse.x=(e.clientX/window.innerWidth)*2-1;
  mouse.y=-(e.clientY/window.innerHeight)*2+1;
});

window.addEventListener('click',function(){
  var meshes=[];
  scene.traverse(function(o){if(o.isMesh)meshes.push(o);});
  raycaster.setFromCamera(mouse,camera);
  var hits=raycaster.intersectObjects(meshes);
  if(hits.length>0){
    var act=getAction(hits[0].object);
    if(act){
      window.parent.postMessage({type:'fpClick',label:act[0],action:act[1]},'*');
      var el=document.getElementById('hud');
      el.textContent='\u2705 '+act[0]+' \u2014 \u5df2\u9001\u51fa';
      el.style.color='#4f4';
      setTimeout(function(){
        el.textContent='\ud83d\udc41 \u9ede\u64ca\u8a2d\u5099\u90e8\u4ef6\u9032\u884c\u6aa2\u67e5';
        el.style.color='#4af';
      },1500);
    }
  }
});

// ── Render loop ──
function animate(){
  requestAnimationFrame(animate);
  controls.update();
  var meshes=[];
  scene.traverse(function(o){if(o.isMesh)meshes.push(o);});
  raycaster.setFromCamera(mouse,camera);
  var hits=raycaster.intersectObjects(meshes);
  if(hoveredMesh){
    hoveredMesh.material=origMats.get(hoveredMesh);
    hoveredMesh=null; tip.style.display='none';
  }
  if(hits.length>0){
    var obj=hits[0].object;
    var act=getAction(obj);
    if(act){
      if(!origMats.has(obj))origMats.set(obj,obj.material);
      obj.material=hlMat; hoveredMesh=obj;
      tip.style.display='block';
      tip.style.left=(window.innerWidth/2+24)+'px';
      tip.style.top=(window.innerHeight/2-32)+'px';
      tip.textContent='\ud83d\udd0d '+act[0]+'  \u2014  \u9ede\u64ca\u6aa2\u67e5';
    }
  }
  renderer.render(scene,camera);
}
animate();

window.addEventListener('resize',function(){
  camera.aspect=window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth,window.innerHeight);
});
</script>
</body>
</html>
"""


def _write_viewer_html(static_dir: Path) -> None:
    """Write viewer.html to static directory so the local HTTP server can serve it."""
    out = static_dir / "viewer.html"
    # surrogate pair (\ud83d\udc41 etc.) → proper Unicode code points before UTF-8
    safe = _VIEWER_HTML.encode("utf-16-le", "surrogatepass").decode("utf-16-le")
    out.write_text(safe, encoding="utf-8")
    print(f"[OK] viewer.html written → {out}")


def _build_threejs_viewer(viewer_url: str) -> str:
    """Return an <iframe src=viewer_url> tag (no srcdoc, no sandbox)."""
    return (f'<iframe src="{viewer_url}" '
            f'style="width:100%;height:580px;border:none;border-radius:12px;" '
            f'referrerpolicy="no-referrer"></iframe>')


def _make_js_bridge() -> str:
    """
    透過 img onload 注入兩件事到 Gradio 父頁面：
    1. window.fpClick(action)  — 更新 textbox 並點按 submit
    2. window.addEventListener('message', ...)  — 接收 iframe postMessage
    """
    return f"""
<img src="{_GIF}" style="display:none;position:absolute;width:0;height:0"
     onload="
(function(){{
  /* fpClick: React setter trick to update Gradio textbox */
  window.fpClick = function(action) {{
    var el = document.querySelector('#fp_input textarea');
    if (!el) return;
    var p = Object.getOwnPropertyDescriptor(
              window.HTMLTextAreaElement.prototype, 'value');
    if (p && p.set) p.set.call(el, action);
    else el.value = action;
    el.dispatchEvent(new Event('input',  {{bubbles:true}}));
    el.dispatchEvent(new Event('change', {{bubbles:true}}));
    setTimeout(function(){{
      var btn = document.querySelector('#fp_submit button');
      if (btn) btn.click();
    }}, 280);
  }};
  /* Receive postMessage from Three.js iframe */
  window.addEventListener('message', function(e){{
    if (e.data && e.data.type === 'fpClick') {{
      window.fpClick(e.data.action);
    }}
  }});
}})();
">
"""


# ══════════════════════════════════════════════════════════════════════════════
# Gradio 介面
# ══════════════════════════════════════════════════════════════════════════════

def create_firstperson_interface(secom_data_path: str, use_ai_mentor: bool = True):
    """建立 Virtual Fab 第一人稱 3D 互動介面。"""

    system = SimulationTrainingSystem(secom_data_path, use_ai_mentor=use_ai_mentor)

    # ── 狀態捕捉（monkey-patch）────────────────────────────────────────────
    _state_holder: dict = {"state": {}}
    _orig_gen = system._generate_equipment_diagram.__func__

    def _patched_gen(self, state):
        _state_holder["state"] = state
        return _orig_gen(self, state)

    system._generate_equipment_diagram = types.MethodType(_patched_gen, system)

    # ── 啟動本地 GLB 伺服器 + 生成 Three.js 檢視器 ─────────────────────────
    if _GLB_PATH.exists():
        glb_port = _start_glb_server(str(_STATIC))
        _write_viewer_html(_STATIC)          # 寫 viewer.html 到 static/
        viewer_url = f"http://127.0.0.1:{glb_port}/viewer.html"
        _viewer_html = _build_threejs_viewer(viewer_url)
        print(f"[OK] Viewer URL: {viewer_url}")
    else:
        _viewer_html = _PLACEHOLDER
        print("[WARN] asml_duv.glb 未找到，3D 檢視器停用")

    # ── 生成故障狀態面板（右側 HMI 區的即時指示燈）──────────────────────
    def _make_status_panel(state: dict) -> str:
        if not state:
            return _DASH_PLACEHOLDER
        viz = system.equipment_visualizer
        cs = viz._calculate_all_status(state)

        ITEMS = [
            ("cooling_system",   "❄️ 冷卻系統"),
            ("light_source",     "💡 光源系統"),
            ("lens_system",      "🔭 投影鏡組"),
            ("wafer_stage",      "💿 晶圓載台"),
            ("alignment_system", "🎯 對準系統"),
            ("reticle_stage",    "📐 光罩載台"),
            ("wafer_handler",    "🦾 晶圓傳送"),
            ("control_panel",    "🖥 控制系統"),
        ]
        rows = ""
        for cid, label in ITEMS:
            s = cs.get(cid, {})
            lvl = s.get("level", "ok")
            if lvl == "critical":
                dot = "#ff4444"; txt = "🔴 嚴重異常"
            elif lvl == "warning":
                dot = "#ffaa00"; txt = "🟡 警告"
            else:
                dot = "#44cc88"; txt = "🟢 正常"
            rows += (f'<div style="display:flex;justify-content:space-between;'
                     f'padding:3px 0;border-bottom:1px solid #0d2040;">'
                     f'<span style="color:#8ab;font-size:11px;">{label}</span>'
                     f'<span style="color:{dot};font-size:11px;">{txt}</span>'
                     f'</div>')

        return (f'<div style="background:#0a1220;border:1px solid #1a4a7c;'
                f'border-radius:8px;padding:10px 12px;">'
                f'<div style="color:#4af;font-size:11px;font-weight:bold;'
                f'letter-spacing:1px;margin-bottom:6px;">⚡ 子系統狀態</div>'
                f'{rows}</div>')

    # ════════════════════════════════════════════════════════════════════════
    with gr.Blocks(title="Virtual Fab — ASML 3D 操作員訓練") as demo:

        gr.HTML(f"<style>{_CSS}</style>")

        # JS Bridge（img onload 注入 fpClick + message listener）
        gr.HTML(_make_js_bridge())

        # ── 標題列 ──────────────────────────────────────────────────────────
        gr.HTML("""
        <div style="background:linear-gradient(135deg,#050d1a,#0d1b2a);
                    border-bottom:2px solid #1a4a7c;padding:12px 20px;
                    display:flex;align-items:center;justify-content:space-between;
                    margin:-8px -8px 10px -8px;">
          <div>
            <div style="color:#4af;font-size:17px;font-weight:bold;letter-spacing:2px;">
              ◈ ASML TWINSCAN NXT:870 — 3D 操作員訓練
            </div>
            <div style="color:#6ab;font-size:11px;margin-top:3px;letter-spacing:1px;">
              Virtual Fab &nbsp;|&nbsp; 第一人稱 3D 視角 &nbsp;|&nbsp;
              旋轉/縮放模型 → 點擊部件 → AI 學長回應
            </div>
          </div>
          <div style="color:#4f4;font-size:11px;text-align:right;">
            <div>● 3D MODEL LOADED</div>
            <div style="color:#6ab;margin-top:2px;">DUV 248 nm KrF</div>
          </div>
        </div>""")

        # ── 難度 + 開始 ──────────────────────────────────────────────────────
        with gr.Row():
            difficulty_dropdown = gr.Dropdown(
                choices=["easy", "medium", "hard"],
                value="medium", label="訓練難度",
                scale=1, min_width=150,
            )
            gr.HTML(
                '<div style="padding:9px 14px;color:#6ab;font-size:12px;">'
                '← 選擇難度後按「▶ 開始新情境」。'
                '用滑鼠<b style="color:#4af;">旋轉/縮放</b> 3D 模型，'
                '游標懸停部件會<b style="color:#ffa500;">橘色高亮</b>，'
                '<b style="color:#ffa500;">點擊</b>即觸發操作。</div>',
                scale=3,
            )
            start_btn = gr.Button("▶ 開始新情境", variant="primary",
                                  scale=1, min_width=155)

        # ── 主畫面：3D 檢視器（左）+ 狀態面板（右）──────────────────────────
        with gr.Row(equal_height=False):

            # 左：Three.js 3D 檢視器（靜態 iframe，永遠顯示）
            with gr.Column(scale=5, min_width=560):
                gr.HTML(value=_viewer_html, label="3D 操作員視角")

            # 右：故障狀態 + HMI 指令按鈕
            with gr.Column(scale=2, min_width=225):

                gr.HTML("""
                <div style="background:linear-gradient(180deg,#0d1b2a,#0a1220);
                            border:1px solid #1a4a7c;border-radius:10px;
                            padding:11px 13px;margin-bottom:6px;">
                  <div style="color:#4af;font-size:12px;font-weight:bold;
                              letter-spacing:1px;margin-bottom:4px;">
                    ⚙ ASML HMI 控制台
                  </div>
                  <div style="display:flex;align-items:center;gap:5px;">
                    <div style="width:7px;height:7px;border-radius:50%;
                                background:#4f4;box-shadow:0 0 5px #4f4;"></div>
                    <div style="color:#4f4;font-size:11px;">SYSTEM ONLINE</div>
                  </div>
                </div>""")

                # 即時子系統狀態燈
                status_panel = gr.HTML(value=_DASH_PLACEHOLDER)

                gr.HTML('<div style="color:#5a8a9a;font-size:11px;margin:8px 0 5px;'
                        'letter-spacing:1px;">── 輔助指令 ──</div>')

                mentor_btn = gr.Button("📞  詢問學長",  variant="primary",
                                       elem_classes="hmi-btn", size="sm")
                stop_btn   = gr.Button("🛑  緊急停機",
                                       elem_classes="hmi-btn hmi-btn-stop", size="sm")

        # ── 即時參數列 ───────────────────────────────────────────────────────
        dashboard_display = gr.HTML(value=_DASH_PLACEHOLDER, label="即時參數監控")

        # ── 隱藏狀態 ─────────────────────────────────────────────────────────
        equipment_display        = gr.HTML(visible=False)
        equipment_status_display = gr.HTML(visible=False)

        # ── 對話歷史 ─────────────────────────────────────────────────────────
        system_messages = gr.Chatbot(label="學長對話 / 系統訊息",
                                     height=320, show_label=True)

        # ── 輸入區 ───────────────────────────────────────────────────────────
        with gr.Row():
            user_input = gr.Textbox(
                label="",
                placeholder="點擊 3D 模型部件自動填入，或直接輸入指令…",
                lines=2, max_lines=3, scale=5, elem_id="fp_input",
            )
            submit_btn = gr.Button("執行 ▶", variant="primary",
                                   scale=1, min_width=90, elem_id="fp_submit")

        with gr.Accordion("📋 操作日誌", open=False):
            action_log = gr.Textbox(label="", lines=8, interactive=False)

        timer = gr.Timer(value=1, active=False)

        # ════════════════════════════════════════════════════════════════════
        # 事件綁定
        # ════════════════════════════════════════════════════════════════════

        def start_scenario(difficulty):
            eq, dash, eq_st, msgs, log = system.start_new_scenario(difficulty)
            sp = _make_status_panel(_state_holder["state"])
            return eq, dash, eq_st, msgs, log, sp, gr.Timer(active=True)

        start_btn.click(
            fn=start_scenario,
            inputs=[difficulty_dropdown],
            outputs=[equipment_display, dashboard_display, equipment_status_display,
                     system_messages, action_log, status_panel, timer],
        )

        def handle_submit(text, eq, dash, eq_st, msgs, log):
            cleared, eq, dash, eq_st, msgs, log = system.process_user_input(
                text, eq, dash, eq_st, msgs, log)
            sp = _make_status_panel(_state_holder["state"])
            return cleared, eq, dash, eq_st, msgs, log, sp

        _sub_in  = [user_input, equipment_display, dashboard_display,
                    equipment_status_display, system_messages, action_log]
        _sub_out = [user_input, equipment_display, dashboard_display,
                    equipment_status_display, system_messages, action_log, status_panel]

        submit_btn.click(fn=handle_submit, inputs=_sub_in, outputs=_sub_out)
        user_input.submit(fn=handle_submit, inputs=_sub_in, outputs=_sub_out)

        def auto_tick(eq, dash, eq_st, msgs, log):
            eq, dash, eq_st, msgs, log = system.auto_progress(eq, dash, eq_st, msgs, log)
            sp = _make_status_panel(_state_holder["state"])
            return eq, dash, eq_st, msgs, log, sp

        timer.tick(
            fn=auto_tick,
            inputs=[equipment_display, dashboard_display,
                    equipment_status_display, system_messages, action_log],
            outputs=[equipment_display, dashboard_display,
                     equipment_status_display, system_messages, action_log, status_panel],
        )

        # 輔助按鈕
        def make_quick(txt):
            def _fn(eq, dash, eq_st, msgs, log):
                cleared, eq, dash, eq_st, msgs, log = system.process_user_input(
                    txt, eq, dash, eq_st, msgs, log)
                sp = _make_status_panel(_state_holder["state"])
                return txt, eq, dash, eq_st, msgs, log, sp
            return _fn

        _hmi_in  = [equipment_display, dashboard_display,
                    equipment_status_display, system_messages, action_log]
        _hmi_out = [user_input, equipment_display, dashboard_display,
                    equipment_status_display, system_messages, action_log, status_panel]

        for btn, txt in [
            (mentor_btn, "學長，目前這個情況該怎麼辦？"),
            (stop_btn,   "緊急停機"),
        ]:
            btn.click(fn=make_quick(txt), inputs=_hmi_in, outputs=_hmi_out)

    return demo
