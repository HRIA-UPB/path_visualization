import os
import re
import json
from pathlib import Path
from pprint import pprint
import shutil

IMG_BASE_PATH = "./"

boxed_pattern = r'\\boxed\{\s*(\[[^\]]+\])\s*\}'


def load_validation_data():
    """Load all validation files and organize data by step and line index."""
    val_files = sorted([(int(file.split('.')[0]), file) for file in os.listdir("./") if file.endswith(".jsonl")])
    
    # Dictionary to store data: {line_index: {step: sample_data}}
    data_by_line = {}
    
    for step, val_file in val_files:
        print(f"Loading {val_file} (step {step})...")
        with open(val_file, 'r') as f:
            for line_idx, line in enumerate(f):

                if line_idx >= 10:
                    break

                if line.strip():
                    sample_dict = json.loads(line)

                    # copy the images to the ./images folder
                    # img_root = "/Users/teo/Desktop/fep/data/"
                    # print(img_root + sample_dict["image_path"])
                    # # check if the file exists
                    # if not os.path.exists(img_root + sample_dict["image_path"]):
                    #     print(f"File does not exist: {img_root + sample_dict['image_path']}")
                        
                    # # copy the image to the ./images folder
                    # shutil.copy(img_root + sample_dict['image_path'], sample_dict['image_path'])
                    
                    if line_idx not in data_by_line:
                        data_by_line[line_idx] = {}

                    # Extract predicted bbox from \boxed{[...] }
                    matches = re.findall(boxed_pattern, sample_dict["output"])
                    sample_dict["predicted"] = ""
                    if matches:
                        try:
                            pred_bbox = matches[-1]
                            pred_bbox_eval = eval(pred_bbox)
                            if len(pred_bbox_eval) == 4:
                                sample_dict["predicted"] = matches[-1]
                        except Exception as e:
                            pass

                    sample_dict["output"] = sample_dict["output"].replace("<think>", "[start_thought]").replace("</think>", "[end_thought]")
                    sample_dict["input"] = sample_dict["input"].replace("<think>", "[start_thought]").replace("</think>", "[end_thought]")
                    
                    
                    data_by_line[line_idx][step] = sample_dict
    return data_by_line, val_files


def generate_html(data_by_line, val_files):
    """Generate HTML file with interactive validation data viewer."""
    
    validation_data_json = json.dumps(data_by_line)
    available_steps_json = json.dumps([step for step, _ in val_files])
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Validation Data Evolution Viewer</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 2000px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2em;
        }}
        .controls {{
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}
        .control-group {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }}
        .control-group label {{
            font-weight: 600;
            color: #495057;
            min-width: 120px;
        }}
        select, input {{
            padding: 8px 12px;
            border: 1px solid #ced4da;
            border-radius: 5px;
            font-size: 14px;
        }}
        select {{
            min-width: 200px;
        }}
        .step-navigation {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        .step-btn {{
            padding: 8px 16px;
            border: 1px solid #007bff;
            background: white;
            color: #007bff;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .step-btn:hover, .step-btn.active {{
            background: #007bff;
            color: white;
        }}
        .content {{
            padding: 20px;
        }}
        .sample-info {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #007bff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-label {{
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
            font-weight: 600;
        }}
        .metric-value {{
            font-size: 18px;
            font-weight: bold;
            color: #495057;
        }}
        .content-section {{
            margin-bottom: 25px;
        }}
        .content-section h3 {{
            color: #495057;
            border-bottom: 2px solid #007bff;
            padding-bottom: 5px;
            margin-bottom: 15px;
        }}
        
        .step-layout {{
            display: flex;
            gap: 20px;
            align-items: flex-start;
        }}
        
        .image-column {{
            flex: 1;
            min-width: 0;
        }}
        
        .text-column {{
            flex: 1;
            min-width: 300px;
        }}
        
        @media (max-width: 768px) {{
            .step-layout {{
                flex-direction: column;
            }}
            
            .text-column {{
                min-width: auto;
            }}
        }}
        
        .text-section {{
            margin-bottom: 20px;
        }}
        
        .text-section h4 {{
            color: #495057;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .text-content-box {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 12px;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            line-height: 1.4;
            max-height: 500px;
            overflow-y: auto;
        }}
        
        .content-box {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.4;
            max-height: 300px;
            overflow-y: auto;
        }}
        .image-info {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 15px;
        }}
        .image-container {{
            margin: 20px 0;
            text-align: center;
        }}
        .image-wrapper {{
            position: relative;
            display: inline-block;
            max-width: 100%;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .validation-image {{
            max-width: 100%;
            height: auto;
            display: block;
            cursor: zoom-in;
            transition: transform 0.3s ease;
        }}
        .validation-image.zoomed {{
            cursor: zoom-out;
        }}
        .bounding-box {{
            position: absolute;
            border: 3px solid;
            background: rgba(0,0,0,0.05);
            pointer-events: none;
        }}
        .bounding-box-label {{
            position: absolute;
            top: -25px;
            left: 0;
            color: white;
            padding: 2px 6px;
            font-size: 12px;
            font-weight: bold;
            border-radius: 3px;
        }}
        .image-controls {{
            margin-top: 10px;
            display: flex;
            gap: 10px;
            justify-content: center;
            align-items: center;
        }}
        .image-controls button {{
            padding: 5px 10px;
            border: 1px solid #007bff;
            background: white;
            color: #007bff;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }}
        .image-controls button:hover, .image-controls button.active {{
            background: #007bff;
            color: white;
        }}
        .no-data {{
            text-align: center;
            color: #6c757d;
            font-style: italic;
            padding: 40px;
        }}
        .evolution-timeline {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            overflow-x: auto;
            padding: 10px 0;
        }}
        .timeline-step {{
            min-width: 100px;
            text-align: center;
            padding: 10px;
            border: 2px solid #dee2e6;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .timeline-step:hover, .timeline-step.active {{
            border-color: #007bff;
            background: #e3f2fd;
        }}
        .step-number {{
            font-weight: bold;
            color: #007bff;
        }}
        .step-reward {{
            font-size: 12px;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Validation Data Evolution Viewer</h1>
            <p>Select a line to view how the sample evolves across training steps</p>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label for="lineSelect">Select Line:</label>
                <select id="lineSelect" onchange="loadLineData()">
                    <option value="">Choose a line...</option>
                </select>
            </div>
            <div class="control-group">
                <label>Available Steps:</label>
                <div class="step-navigation" id="stepNavigation"></div>
            </div>
        </div>
        
        <div class="content" id="content">
            <div class="no-data">
                Please select a line to view the validation data evolution.
            </div>
        </div>
    </div>

    <script>
        const validationData = {validation_data_json};
        const availableSteps = {available_steps_json};

        function initializePage() {{
            const lineSelect = document.getElementById('lineSelect');
            const lineCount = Object.keys(validationData).length;
            for (let i = 0; i < lineCount; i++) {{
                const option = document.createElement('option');
                option.value = i;
                option.textContent = `Line ${{i + 1}}`;
                lineSelect.appendChild(option);
            }}
            updateStepNavigation();
        }}

        function updateStepNavigation() {{
            const stepNav = document.getElementById('stepNavigation');
            stepNav.innerHTML = '';
            availableSteps.forEach(step => {{
                const btn = document.createElement('button');
                btn.className = 'step-btn';
                btn.textContent = `Step ${{step}}`;
                btn.onclick = () => showStep(step);
                stepNav.appendChild(btn);
            }});
        }}

        function loadLineData() {{
            const idx = parseInt(document.getElementById('lineSelect').value);
            if (idx >= 0 && validationData[idx]) {{
                showLineEvolution(idx);
            }}
        }}

        function showLineEvolution(idx) {{
            const data = validationData[idx];
            const steps = Object.keys(data).map(Number).sort((a,b)=>a-b);
            let html = `<div class="sample-info"><h2>Line ${{idx+1}} Evolution</h2><p>Steps: ${{steps.join(', ')}}</p></div><div class="evolution-timeline">`;
            steps.forEach(s=>{{
                const sample=data[s];
                html+=`<div class="timeline-step" onclick="showStep(${{s}})"><div class="step-number">Step ${{s}}</div><div class="step-reward">Reward: ${{(sample.reward||0).toFixed(3)}}</div></div>`;
            }});
            html+='</div>';
            html+=showStepData(data[steps[0]],steps[0]);
            document.getElementById('content').innerHTML=html;
        }}

        function showStep(step) {{
            const idx=parseInt(document.getElementById('lineSelect').value);
            if(idx>=0&&validationData[idx]&&validationData[idx][step]) {{
                document.querySelectorAll('.step-btn').forEach(b=>b.classList.remove('active'));
                document.querySelectorAll('.timeline-step').forEach(b=>b.classList.remove('active'));
                document.querySelectorAll('.step-btn, .timeline-step').forEach(b=>{{if(b.textContent.includes(`Step ${{step}}`))b.classList.add('active');}});
                
                // Find and update only the step data section, preserving the timeline
                const content = document.querySelector('.content');
                const existingContent = content.innerHTML;
                const stepDataStart = existingContent.indexOf('<div class="content-section">');
                
                if (stepDataStart !== -1) {{
                    content.innerHTML = existingContent.substring(0, stepDataStart) + showStepData(validationData[idx][step],step);
                }} else {{
                    content.innerHTML = existingContent + showStepData(validationData[idx][step],step);
                }}
            }}
        }}

        function showStepData(sample,step){{
            const fmt=t=>t?t.replace(/\\n/g,'\\n').replace(/\\t/g,'\\t'):'N/A';
            const imgPath=sample.image_path||''; const fullPath=imgPath?'{IMG_BASE_PATH}'+imgPath:'';
            return `<div class="content-section"><h3>Step ${{step}}</h3>
            <div class="metrics">
                <div class="metric-card"><div class="metric-label">Reward</div><div class="metric-value">${{(sample.reward||0).toFixed(3)}}</div></div>
                <div class="metric-card"><div class="metric-label">Format</div><div class="metric-value">${{(sample.format_reward||0).toFixed(3)}}</div></div>
                <div class="metric-card"><div class="metric-label">Accuracy</div><div class="metric-value">${{(sample.acc_reward||0).toFixed(3)}}</div></div>
            </div>
            <div class="image-info"><strong>Image:</strong> ${{sample.image_path||'N/A'}}</div>
            
            <div class="step-layout">
                <div class="image-column">
                    ${{fullPath?`<div class="image-container"><div class="image-wrapper" id="imageWrapper">
                    <img src="${{fullPath}}" class="validation-image" id="validationImage"
                    onload="drawBoundingBoxes('${{sample.gts}}','${{sample.predicted}}')" onerror="handleImageError()" onclick="toggleImageZoom()">
                    </div>
                    <div class="image-controls">
                        <button onclick="toggleBoxType('gt')" id="gtToggle" class="active">Hide GT Box</button>
                        <button onclick="toggleBoxType('pred')" id="predToggle" class="active">Hide Pred Box</button>
                        <button onclick="toggleImageZoom()" id="zoomToggle">Zoom In</button>
                        <button onclick="resetImageZoom()">Reset</button>
                    </div></div>`:'<div class="no-data">No image available</div>'}}
                </div>
                
                <div class="text-column">
                    <div class="text-section">
                        <h4>Ground Truth</h4>
                        <div class="text-content-box">${{fmt(sample.gts)}}</div>
                    </div>
                    
                    <div class="text-section">
                        <h4>Predicted Bounding Box</h4>
                        <div class="text-content-box">${{fmt(sample.predicted || 'No prediction found')}}</div>
                    </div>
                    
                    <div class="text-section">
                        <h4>Input</h4>
                        <div class="text-content-box">${{fmt(sample.input)}}</div>
                    </div>
                    
                    <div class="text-section">
                        <h4>Output</h4>
                        <div class="text-content-box">${{fmt(sample.output)}}</div>
                    </div>
                </div>
            </div>
            </div>`;
        }}

        function parseBBox(str){{
            if(!str)return null;try{{let arr=JSON.parse(str);if(Array.isArray(arr)&&arr.length===4)return arr;}}
            catch(e){{try{{let arr=eval(str);if(Array.isArray(arr)&&arr.length===4)return arr;}}catch{{}}}}return null;
        }}

        function drawBoundingBoxes(gtStr,predStr){{
            const wrap=document.getElementById('imageWrapper');const img=document.getElementById('validationImage');
            if(!img||!wrap)return;
            wrap.querySelectorAll('.bounding-box').forEach(b=>b.remove());
            const gt=parseBBox(gtStr),pred=parseBBox(predStr);
            const scaleX=img.clientWidth/img.naturalWidth,scaleY=img.clientHeight/img.naturalHeight;
            if(gt)createBox(gt,'#007bff','Ground Truth');
            if(pred)createBox(pred,'#ff0000','Predicted');

            function createBox(b,color,label){{
                const [x1,y1,x2,y2]=b;const box=document.createElement('div');
                box.className='bounding-box';
                box.style.borderColor=color;
                box.style.background=color==='blue'?'rgba(0,123,255,0.1)':'rgba(255,0,0,0.1)';
                box.style.left=(x1*scaleX)+'px';box.style.top=(y1*scaleY)+'px';
                box.style.width=((x2-x1)*scaleX)+'px';box.style.height=((y2-y1)*scaleY)+'px';
                const lbl=document.createElement('div');lbl.className='bounding-box-label';lbl.style.background=color;lbl.textContent=label;
                box.appendChild(lbl);wrap.appendChild(box);
            }}
        }}

        function toggleBoxType(type){{
            const label=type==='gt'?'Ground Truth':'Predicted';
            const boxes=Array.from(document.querySelectorAll('.bounding-box-label')).filter(el=>el.textContent===label).map(el=>el.parentElement);
            const toggle=document.getElementById(type==='gt'?'gtToggle':'predToggle');
            if(!boxes.length)return;
            const hidden=boxes[0].style.display==='none';
            boxes.forEach(b=>b.style.display=hidden?'block':'none');
            toggle.textContent=hidden?`Hide ${{type==='gt'?'GT':'Pred'}} Box`:`Show ${{type==='gt'?'GT':'Pred'}} Box`;
            toggle.classList.toggle('active',hidden);
        }}

        function toggleImageZoom(){{
            const img=document.getElementById('validationImage');
            const t=document.getElementById('zoomToggle');
            if(img.classList.contains('zoomed')){{img.style.transform='scale(1)';img.classList.remove('zoomed');t.textContent='Zoom In';}}
            else{{img.style.transform='scale(2)';img.classList.add('zoomed');t.textContent='Zoom Out';}}
            img.style.transformOrigin='center';
        }}

        function resetImageZoom(){{
            const img=document.getElementById('validationImage');const t=document.getElementById('zoomToggle');
            if(img){{img.style.transform='scale(1)';img.classList.remove('zoomed');if(t)t.textContent='Zoom In';}}
        }}

        function handleImageError(){{document.getElementById('imageWrapper').innerHTML='<div class="no-data">Failed to load image</div>';}}
        window.onload=initializePage;
    </script>
</body>
</html>
    """
    return html_content


# === MAIN EXECUTION ===
data_by_line, val_files = load_validation_data()
html_output = generate_html(data_by_line, val_files)
Path("index.html").write_text(html_output, encoding="utf-8")
print("✅ HTML file generated: index.html")
