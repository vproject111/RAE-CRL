from datetime import datetime, timedelta
from uuid import UUID, uuid4
import json

from fastapi import Request
from nicegui import ui

from apps.crl.core.database import get_session
from apps.crl.core.models import (ArtifactStatus, ArtifactType,
                                  ArtifactVisibility, BaseArtifact,
                                  ArtifactRelation)
from apps.crl.services.export_service import ExportService
from apps.crl.services.ingestion_service import IngestionService
from apps.crl.services.rae_client import RAEClient
from apps.crl.services.storage.sql import SQLRepository
from apps.crl.services.watchdog_service import WatchdogService

# Helper to run async DB ops
async def run_db(func):
    async for session in get_session():
        repo = SQLRepository(session)
        return await func(repo)

@ui.page("/")
async def main_page(request: Request):
    # --- STYLES, FONTS & WCGA INLINE CONFIG ---
    ui.add_head_html('''
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <script>
        // Left-shifted WCGA initialization to prevent page load flash (FOUC)
        (function() {
            if (localStorage.getItem('wcgaKontrast') === '1') {
                document.documentElement.classList.add('wcga-contrast');
            }
            if (localStorage.getItem('wcgaFonts') === '1') {
                document.documentElement.classList.add('wcga-fonts');
            }
        })();
    </script>
    <style>
        body {
            font-family: 'Outfit', sans-serif;
            background-color: #050608;
            color: #e2e8f0;
            margin: 0;
            overflow: hidden;
        }
        .code-font {
            font-family: 'JetBrains Mono', monospace;
        }
        .glass-card {
            background: rgba(15, 23, 42, 0.45);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
        }
        .neon-border-cyan {
            border: 1px solid rgba(6, 182, 212, 0.25);
        }
        .neon-border-violet {
            border: 1px solid rgba(139, 92, 246, 0.25);
        }
        .glow-text-cyan {
            text-shadow: 0 0 8px rgba(6, 182, 212, 0.5);
        }
        .glow-text-violet {
            text-shadow: 0 0 8px rgba(139, 92, 246, 0.5);
        }
        
        /* --- ACCESSIBILITY / WCGA CONTRAST OVERRIDES --- */
        .wcga-contrast body {
            background-color: #ffffff !important;
            color: #000000 !important;
        }
        .wcga-contrast .glass-card {
            background: #ffffff !important;
            border: 2px solid #000000 !important;
            color: #000000 !important;
        }
        .wcga-contrast .text-white, 
        .wcga-contrast .text-slate-300, 
        .wcga-contrast .text-slate-400 {
            color: #000000 !important;
        }
        .wcga-contrast .text-purple-400, 
        .wcga-contrast .text-cyan-400 {
            color: #1e1b4b !important;
            font-weight: bold !important;
        }
        .wcga-contrast .glow-text-cyan, 
        .wcga-contrast .glow-text-violet {
            text-shadow: none !important;
            color: #000000 !important;
        }
        .wcga-contrast .bg-slate-950, 
        .wcga-contrast .bg-slate-900/60,
        .wcga-contrast .bg-slate-950/90,
        .wcga-contrast .bg-slate-950/80 {
            background-color: #f8fafc !important;
            border-color: #000000 !important;
            color: #000000 !important;
        }
        .wcga-contrast input, 
        .wcga-contrast textarea, 
        .wcga-contrast select {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 2px solid #000000 !important;
        }
        .wcga-contrast .q-field__native,
        .wcga-contrast .q-field__label,
        .wcga-contrast .q-select__selection {
            color: #000000 !important;
        }
        
        /* --- ACCESSIBILITY / WCGA FONTS OVERRIDES --- */
        .wcga-fonts body {
            font-size: 1.25rem !important;
        }
        .wcga-fonts .text-xs {
            font-size: 0.95rem !important;
        }
        .wcga-fonts .text-sm {
            font-size: 1.15rem !important;
        }
        .wcga-fonts .text-lg {
            font-size: 1.45rem !important;
        }
        .wcga-fonts .text-2xl {
            font-size: 2.1rem !important;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #050608;
        }
        ::-webkit-scrollbar-thumb {
            background: #1e293b;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #334155;
        }
    </style>
    ''')

    # --- STATE ---
    project = "default-lab"
    rae_client = RAEClient()
    
    # Conflict banner state
    active_conflicts = []
    
    # Selected Node for Inspector
    selected_node_id = None

    # Cookie Acceptance check from request
    cookie_accepted = request.cookies.get('cookieAccepted') == 'true'

    # Load data helpers
    async def load_traces():
        async def _get(repo):
            return await repo.list_by_project(project, type=ArtifactType.TRACE)
        return await run_db(_get)

    async def load_all_artifacts():
        async def _get(repo):
            return await repo.list_by_project(project)
        return await run_db(_get)

    # --- ACTIONS ---
    async def add_quick_capture():
        content = quick_input.value
        title_val = quick_title.value
        art_type = type_select.value
        grace_hours = int(grace_slider.value)
        author_val = author_input.value or "Dr. Grzegorz"
        
        if not content or not title_val or not art_type:
            ui.notify("Fill in title, type and content details!", type="warning")
            return

        async def _save(repo):
            artifact = BaseArtifact(
                type=ArtifactType(art_type),
                title=title_val,
                description=content,
                project=project,
                status=ArtifactStatus.DRAFT if art_type == ArtifactType.TRACE.value else ArtifactStatus.ACTIVE,
                visibility=ArtifactVisibility.PRIVATE,
                grace_period_end=datetime.utcnow() + timedelta(hours=grace_hours) if grace_hours > 0 else None,
                author=author_val,
            )
            await repo.save(artifact)
            
            # Run Watchdog Check on new observations
            if artifact.type == ArtifactType.OBSERVATION:
                watchdog = WatchdogService(rae_client, repo)
                conflict = await watchdog.check_consistency(artifact)
                if conflict:
                    active_conflicts.append(f"Conflict on Observation '{artifact.title}': {conflict}")
                    conflict_banner.refresh()
                    ui.notify("⚠️ Watchdog: logical contradiction detected!", type="negative", duration=8)
            
        await run_db(_save)
        quick_input.value = ""
        quick_title.value = ""
        ui.notify(f"{art_type.upper()} captured successfully! 🧠", type="positive")
        await refresh_all()

    async def refine_trace(artifact):
        async def _get_potential_parents(repo):
            return await repo.list_by_project(project)
        
        parents = await run_db(_get_potential_parents)
        parent_options = {str(p.id): f"[{p.type.upper()}] {p.title}" for p in parents if p.id != artifact.id and p.type != ArtifactType.TRACE}

        with ui.dialog() as dialog, ui.card().classes('glass-card neon-border-violet text-white w-96'):
            ui.label(f"Refine Trace: {artifact.title}").classes('text-h6 text-purple-400')
            
            new_type = ui.select(
                options=[t.value for t in ArtifactType if t != ArtifactType.TRACE],
                label="Convert to Type",
                value=ArtifactType.HYPOTHESIS.value
            ).classes('w-full').props('dark outlined')
            
            new_title = ui.input(label="Title", value=artifact.title).classes('w-full').props('dark outlined')
            new_desc = ui.textarea(label="Description", value=artifact.description).classes('w-full').props('dark outlined')
            
            link_to = ui.select(options=parent_options, label="Link to Parent (Optional)").classes('w-full').props('dark outlined')

            async def save_refinement():
                if not new_type.value:
                    ui.notify("Select a type!", type="warning")
                    return
                
                async def _update(repo):
                    art = await repo.get(artifact.id)
                    art.type = ArtifactType(new_type.value)
                    art.title = new_title.value
                    art.description = new_desc.value
                    art.status = ArtifactStatus.ACTIVE
                    art.grace_period_end = None # Ready for Sync
                    await repo.save(art)
                    
                    if link_to.value:
                        from uuid import UUID
                        await repo.link_artifacts(UUID(link_to.value), artifact.id, "supports")
                    
                    # Watchdog Check
                    if art.type == ArtifactType.OBSERVATION:
                        watchdog = WatchdogService(rae_client, repo)
                        conflict = await watchdog.check_consistency(art)
                        if conflict:
                            active_conflicts.append(f"Conflict on Observation '{art.title}': {conflict}")
                            conflict_banner.refresh()
                            ui.notify(f"⚠️ LOGICAL CONFLICT DETECTED: {conflict}", type="warning", duration=10)
                
                await run_db(_update)
                ui.notify("Artifact Refined & Activated!", type="positive")
                dialog.close()
                await refresh_all()

            with ui.row().classes('w-full justify-end q-mt-md'):
                ui.button('Cancel', on_click=dialog.close).props('flat text-color=white')
                ui.button('Refine & Publish', on_click=save_refinement).props('color=purple')
        
        dialog.open()

    async def delete_artifact(artifact_id):
        async def _del(repo):
            art = await repo.get(artifact_id)
            if art:
                await repo.session.delete(art)
                await repo.session.commit()
        await run_db(_del)
        ui.notify("Artifact removed.", type="info")
        await refresh_all()

    async def trigger_sync():
        from apps.crl.services.sync_service import SyncEngine
        engine = SyncEngine()
        ui.notify("Sync started with RAE Core...", type="ongoing")
        try:
            await engine.run_sync_cycle()
            ui.notify("Sync complete! 🚀", type="positive")
            await refresh_all()
        except Exception as e:
            ui.notify(f"Sync failed: {e}", type="negative")

    async def handle_upload(e):
        for file in e.files:
            content = file.content.read().decode('utf-8')
            observation = IngestionService.create_observation_from_file(file.name, content, project)
            
            async def _save(repo):
                await repo.save(observation)
                # Watchdog Check
                watchdog = WatchdogService(rae_client, repo)
                conflict = await watchdog.check_consistency(observation)
                if conflict:
                    active_conflicts.append(f"Conflict on Data Import '{observation.title}': {conflict}")
                    conflict_banner.refresh()
                    ui.notify(f"⚠️ DATA CONFLICT: {conflict}", type="warning", duration=10)
            
            await run_db(_save)
            ui.notify(f"Imported {file.name} successfully! 🧪", type="positive")
        await refresh_all()

    # --- WCGA CONTROLS CLIENT-SIDE ACTIONS ---
    def toggle_wcga_contrast():
        ui.run_javascript('''
            const hasContrast = document.documentElement.classList.toggle("wcga-contrast");
            localStorage.setItem("wcgaKontrast", hasContrast ? "1" : "0");
        ''')
        ui.notify("Contrast mode toggled! 🌓")

    def toggle_wcga_fonts():
        ui.run_javascript('''
            const hasFonts = document.documentElement.classList.toggle("wcga-fonts");
            localStorage.setItem("wcgaFonts", hasFonts ? "1" : "0");
        ''')
        ui.notify("Large text mode toggled! 🔍")

    # --- COOKIE BANNER ACTION ---
    def accept_cookies():
        ui.run_javascript('document.cookie = "cookieAccepted=true; max-age=2592000; path=/";')
        cookie_banner_container.set_visibility(False)
        ui.notify("Cookies accepted. Thank you! 🍪")

    # --- REFRESH HELPER ---
    async def refresh_all():
        await refresh_inbox()
        await update_graph_view()
        await refresh_compiler_preview()
        node_inspector_panel.refresh()

    # --- WORKSPACE LAYOUT ---

    # Real-time Warning Banner (Watchdog)
    @ui.refreshable
    def conflict_banner():
        if active_conflicts:
            with ui.row().classes('w-full bg-red-950/80 border-b border-red-500/40 q-py-sm q-px-md items-center justify-between'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('warning', color='red').classes('text-lg')
                    ui.label(f"WARNING: {active_conflicts[-1]}").classes('text-red-300 font-medium text-sm')
                with ui.row().classes('gap-2'):
                    ui.button("Clear Warnings", on_click=lambda: (active_conflicts.clear(), conflict_banner.refresh())).props('flat dense size=sm color=white')
    
    conflict_banner()

    # Header Portal Bar
    with ui.row().classes('w-full bg-slate-950/90 border-b border-white/10 q-px-md q-py-sm items-center justify-between'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('science', size='24px', color='cyan').classes('glow-text-cyan')
            ui.label("RAE-CRL : Cognitive Lab Desk").classes('text-lg font-bold text-white tracking-wide')
        
        # Telemetry / Drift Alert Indicator
        with ui.row().classes('items-center gap-4 bg-slate-900/60 q-px-md q-py-xs rounded-full border border-white/5'):
            with ui.row().classes('items-center gap-1'):
                ui.badge(color='green').classes('w-2 h-2 rounded-full p-0 q-mr-xs')
                ui.label("Drift Score (PSI): 0.08").classes('text-xs text-slate-400')
            with ui.row().classes('items-center gap-1'):
                ui.badge(color='cyan').classes('w-2 h-2 rounded-full p-0 q-mr-xs')
                ui.label("AIMS Status: COMPLIANT").classes('text-xs text-cyan-400')
                
        with ui.row().classes('gap-2 items-center'):
            # WCGA Buttons
            ui.button(icon="contrast", on_click=toggle_wcga_contrast).props('flat round size=sm color=white').tooltip("Toggle Contrast Mode (WCGA)")
            ui.button(icon="format_size", on_click=toggle_wcga_fonts).props('flat round size=sm color=white').tooltip("Toggle Large Text Size (WCGA)")
            
            ui.separator().props('vertical').classes('bg-white/10 h-6 q-mx-sm')
            
            ui.button("Sync RAE Core", icon="sync", on_click=trigger_sync).props('color=cyan size=sm').classes('code-font')
            ui.button("Quantum Portal", icon="open_in_new", on_click=lambda: ui.open("http://localhost:8080/")).props('flat dense size=sm color=white')

    # Main Left Navigation & View Panels Splitter
    with ui.splitter(value=18).classes('w-full h-screen bg-slate-950 text-slate-300') as splitter:
        with splitter.before:
            with ui.column().classes('w-full h-full bg-slate-950/80 border-r border-white/5 q-py-md'):
                with ui.tabs().props('vertical').classes('w-full text-left') as tabs:
                    desk_tab = ui.tab('Desk', icon='inbox').classes('w-full justify-start text-sm text-slate-400')
                    graph_tab = ui.tab('Graph', icon='hub').classes('w-full justify-start text-sm text-slate-400')
                    mesh_tab = ui.tab('Mesh', icon='language').classes('w-full justify-start text-sm text-slate-400')
                    runner_tab = ui.tab('Runner', icon='psychology').classes('w-full justify-start text-sm text-slate-400')
                    compiler_tab = ui.tab('Compiler', icon='article').classes('w-full justify-start text-sm text-slate-400')
                
        with splitter.after:
            with ui.column().classes('w-full h-full bg-transparent overflow-y-auto'):
                with ui.tab_panels(tabs, value=desk_tab).classes('w-full h-full bg-transparent q-pa-lg') as panels:
                    
                    # --- TAB 1: DESK (Epistemic Sandbox) ---
                    with ui.tab_panel(desk_tab).classes('gap-6'):
                        with ui.row().classes('w-full justify-between items-center q-mb-md'):
                            ui.label("Epistemic Sandbox").classes('text-2xl font-bold text-white')
                            ui.badge("Workspace active: default-lab").props('color=purple')
                        
                        with ui.grid(columns=2).classes('w-full gap-6'):
                            # Quick Capture Card
                            with ui.card().classes('glass-card neon-border-violet text-white q-pa-md'):
                                ui.label("Quick Capture 2.0").classes('text-lg font-bold text-purple-400 q-mb-sm')
                                
                                quick_title = ui.input(placeholder="Title of discovery...").classes('w-full q-mb-sm').props('dark outlined dense')
                                
                                with ui.row().classes('w-full gap-2 q-mb-sm'):
                                    type_select = ui.select(
                                        options=[t.value for t in ArtifactType],
                                        label="Artifact Type",
                                        value=ArtifactType.TRACE.value
                                    ).classes('flex-grow').props('dark outlined dense')
                                    
                                    author_input = ui.input(label="Researcher", placeholder="Dr. Grzegorz").classes('w-32').props('dark outlined dense')
                                    
                                quick_input = ui.textarea(placeholder="Capture messy thoughts, raw findings or structured equations...").classes('w-full q-mb-sm').props('dark outlined rows=3')
                                
                                with ui.column().classes('w-full gap-0 q-mb-md'):
                                    ui.label("Epistemic Grace Period").classes('text-xs text-purple-300 font-medium')
                                    grace_slider = ui.slider(min=0, max=48, value=24).props('label-always color=purple')
                                    ui.label("Hours protected from peer synchronization/Mesh.").classes('text-xs text-slate-400')
                                
                                ui.button("Store in Sandbox", icon="add_circle", on_click=add_quick_capture).props('color=purple').classes('w-full')
                                
                            # Drag & Drop Ingestion Bridge Card
                            with ui.card().classes('glass-card neon-border-cyan text-white q-pa-md'):
                                ui.label("Ingestion Bridge").classes('text-lg font-bold text-cyan-400 q-mb-xs')
                                ui.label("Upload experimental logs, CSV results, or text files directly into cognitive storage.").classes('text-xs text-slate-400 q-mb-md')
                                
                                ui.upload(
                                    label="Drop files (CSV/TXT)",
                                    multiple=True,
                                    auto_upload=True,
                                    on_upload=handle_upload
                                ).classes('w-full h-44 bg-slate-900/60 border border-dashed border-cyan-500/30 rounded-lg').props('dark flat')

                        # Inbox Traces List
                        ui.label("Capture Inbox (Grace Period Active)").classes('text-lg font-bold text-white q-mt-lg q-mb-sm')
                        
                        @ui.refreshable
                        async def refresh_inbox():
                            inbox_container.clear()
                            traces = await load_traces()
                            with inbox_container:
                                if not traces:
                                    ui.label("No pending draft traces in inbox. Ready for new input.").classes('text-slate-500 italic text-sm')
                                for t in traces:
                                    with ui.card().classes('glass-card border border-white/5 w-full q-pa-md hover:border-purple-500/20 transition-all'):
                                        with ui.row().classes('w-full justify-between items-center no-wrap'):
                                            with ui.column().classes('gap-1'):
                                                ui.label(t.title).classes('text-base font-medium text-white')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.badge("TRACE", color='grey-8').classes('text-xs')
                                                    ui.label(f"Author: {t.author} • Captured at {t.created_at.strftime('%H:%M:%S')}").classes('text-xs text-slate-400')
                                            with ui.row().classes('gap-2'):
                                                ui.button(icon="edit_note", on_click=lambda _, a=t: refine_trace(a)).props('color=purple dense flat round').tooltip("Refine and publish")
                                                ui.button(icon="delete", on_click=lambda _, a=t: delete_artifact(a.id)).props('color=red dense flat round').tooltip("Delete trace")
                                        ui.separator().classes('q-my-sm border-white/5')
                                        ui.label(t.description).classes('text-sm text-slate-300 line-clamp-2')

                        inbox_container = ui.column().classes('w-full gap-2')
                        await refresh_inbox()

                    # --- TAB 2: GRAPH (Cognitive Reasoning Graph) ---
                    with ui.tab_panel(graph_tab).classes('gap-6'):
                        ui.label("Cognitive Reasoning Graph").classes('text-2xl font-bold text-white q-mb-md')
                        
                        with ui.grid(columns=3).classes('w-full gap-6 h-full'):
                            # Left side: interactive graph render
                            with ui.card().classes('glass-card border border-white/10 col-span-2 h-[550px] overflow-auto q-pa-md'):
                                ui.label("Visual Provenance DAG").classes('text-sm font-bold text-cyan-400 q-mb-sm')
                                graph_area = ui.mermaid("graph TD\n  Start[Start Research]")
                            
                            # Right side: Node List and Inspector Drawer
                            with ui.card().classes('glass-card border border-white/10 h-[550px] q-pa-md flex flex-col justify-between'):
                                ui.label("Logical Node Inspector").classes('text-sm font-bold text-purple-400 q-mb-sm')
                                
                                @ui.refreshable
                                def node_inspector_panel():
                                    # We'll trigger this panel's content based on selected_node_id
                                    async def load_details():
                                        if not selected_node_id:
                                            return None
                                        async def _get(repo):
                                            return await repo.get(UUID(selected_node_id))
                                        return await run_db(_get)
                                    
                                    # Run synchronously for NiceGUI refresh
                                    import asyncio
                                    try:
                                        loop = asyncio.get_event_loop()
                                        node = loop.run_until_complete(load_details()) if selected_node_id else None
                                    except Exception:
                                        node = None
                                        
                                    if not node:
                                        ui.label("Select a node from the explorer list below to review details.").classes('text-slate-500 italic text-sm')
                                    else:
                                        with ui.column().classes('w-full gap-2 text-white'):
                                            with ui.row().classes('items-center justify-between w-full'):
                                                ui.badge(node.type.upper(), color='purple' if node.type == ArtifactType.HYPOTHESIS else 'cyan')
                                                ui.label(node.author).classes('text-xs text-slate-400')
                                            ui.label(node.title).classes('text-lg font-bold text-white')
                                            ui.separator().classes('border-white/5')
                                            ui.label(node.description).classes('text-sm text-slate-300 h-28 overflow-y-auto')
                                            ui.separator().classes('border-white/5')
                                            
                                            with ui.column().classes('gap-1'):
                                                ui.label(f"UUID: {node.id}").classes('text-xs text-slate-400 code-font')
                                                ui.label(f"Provenance Hash: {node.provenance_hash or 'Not calculated'}").classes('text-xs text-slate-400 code-font')
                                                ui.label(f"Created: {node.created_at.strftime('%Y-%m-%d %H:%M')}").classes('text-xs text-slate-400')
                                                
                                            # Render metadata blob
                                            if node.metadata_blob:
                                                ui.label("Metadata Blob").classes('text-xs font-bold text-purple-300 q-mt-xs')
                                                ui.json(node.metadata_blob).classes('text-xs bg-slate-900/60 p-2 rounded max-h-24 overflow-y-auto')
                                                
                                            ui.button("Delete Node", icon="delete", on_click=lambda: delete_artifact(node.id)).props('color=red flat dense size=sm').classes('q-mt-md')
                                
                                node_inspector_panel()
                                
                                # Real-time list of all active artifacts to select from
                                ui.separator().classes('border-white/5 q-my-sm')
                                ui.label("Node Explorer").classes('text-xs text-slate-400 uppercase tracking-wider')
                                
                                @ui.refreshable
                                async def node_explorer_list():
                                    explorer_container.clear()
                                    arts = await load_all_artifacts()
                                    with explorer_container:
                                        for a in arts:
                                            if a.type == ArtifactType.TRACE: continue
                                            async def on_select(x=a.id):
                                                nonlocal selected_node_id
                                                selected_node_id = str(x)
                                                node_inspector_panel.refresh()
                                                
                                            with ui.item(on_click=on_select).classes('cursor-pointer hover:bg-white/5 rounded q-pa-xs border-b border-white/5 w-full'):
                                                with ui.row().classes('items-center gap-2 no-wrap w-full'):
                                                    # Color badge for type
                                                    color = 'purple' if a.type == ArtifactType.HYPOTHESIS else 'cyan' if a.type == ArtifactType.OBSERVATION else 'amber'
                                                    ui.badge(a.type.upper()[:4], color=color).classes('text-[10px]')
                                                    ui.label(a.title).classes('text-xs text-white truncate max-w-44')
                                                    
                                explorer_container = ui.column().classes('w-full gap-1 h-36 overflow-y-auto')
                                await node_explorer_list()

                        async def update_graph_view():
                            async def _get_data(repo):
                                return await repo.list_by_project(project), await repo.list_relations(project)
                            arts, rels = await run_db(_get_data)
                            if not arts: return
                            
                            code_str = "graph TD\n"
                            # Styles
                            code_str += "  classDef hypothesis fill:#2e1065,stroke:#8b5cf6,stroke-width:2px,color:#fff;\n"
                            code_str += "  classDef observation fill:#083344,stroke:#06b6d4,stroke-width:2px,color:#fff;\n"
                            code_str += "  classDef generic fill:#1e293b,stroke:#475569,stroke-width:1px,color:#fff;\n"
                            
                            # Nodes
                            for art in arts:
                                if art.type == ArtifactType.TRACE: continue
                                clean_title = art.title.replace('"', "'").replace("\n", " ")[:20]
                                node_id = str(art.id).replace("-", "")
                                code_str += f'  {node_id}["[{art.type.upper()}]<br/>{clean_title}"]\n'
                                # Apply class style
                                style_class = "hypothesis" if art.type == ArtifactType.HYPOTHESIS else "observation" if art.type == ArtifactType.OBSERVATION else "generic"
                                code_str += f'  class {node_id} {style_class};\n'
                            
                            # Edges
                            for rel in rels:
                                s = str(rel.source_id).replace("-", "")
                                t = str(rel.target_id).replace("-", "")
                                code_str += f'  {s} --> {t}\n'
                                
                            graph_area.content = code_str
                            await node_explorer_list()
                        
                        await update_graph_view()

                    # --- TAB 3: MESH (Wymiana CMT i Federacja Pamięci) ---
                    with ui.tab_panel(mesh_tab).classes('gap-6'):
                        ui.label("RAE-Mesh Exchange & Consensual Memory Transfer").classes('text-2xl font-bold text-white q-mb-md')
                        
                        with ui.grid(columns=2).classes('w-full gap-6'):
                            # Peer Map Card
                            with ui.card().classes('glass-card border border-white/10 text-white q-pa-md'):
                                ui.label("Active Mesh Peers").classes('text-lg font-bold text-cyan-400 q-mb-sm')
                                ui.label("Verifiable peer network nodes configured via RAE-Mesh overlay.").classes('text-xs text-slate-400 q-mb-md')
                                
                                # Peer Grid
                                peers = [
                                    {"name": "Node 1 (Lumina)", "ip": "100.68.166.117:8000", "status": "Offline (Timeout)", "score": "0.98", "key": "ssh-ed25519 AAAAC3Nza..."},
                                    {"name": "Node 2 (Julka)", "ip": "100.70.32.40:8000", "status": "Online", "score": "0.95", "key": "ssh-ed25519 AAAAC3Nza..."},
                                    {"name": "Node 3 (Piotrek)", "ip": "172.30.15.11:11434", "status": "Online", "score": "0.99", "key": "ssh-ed25519 AAAAC3Nza..."}
                                ]
                                
                                for p in peers:
                                    with ui.card().classes('bg-slate-900/60 border border-white/5 w-full q-pa-sm q-mb-sm'):
                                        with ui.row().classes('w-full justify-between items-center'):
                                            with ui.column().classes('gap-1'):
                                                ui.label(p["name"]).classes('text-sm font-bold')
                                                ui.label(f"Endpoint: {p['ip']}").classes('text-xs text-slate-400 code-font')
                                            with ui.column().classes('items-end gap-1'):
                                                status_color = "red" if "Offline" in p["status"] else "green"
                                                ui.badge(p["status"], color=status_color).classes('text-[10px]')
                                                ui.label(f"Trust: {p['score']}").classes('text-xs text-slate-400')
                            
                            # CMT Consent Gate Card
                            with ui.card().classes('glass-card border border-white/10 text-white q-pa-md'):
                                ui.label("CMT Consent Registry").classes('text-lg font-bold text-purple-400 q-mb-xs')
                                ui.label("Manage incoming/outgoing memory transfers. Data classified as RESTRICTED is quarantined.").classes('text-xs text-slate-400 q-mb-md')
                                
                                with ui.row().classes('items-center justify-between w-full bg-purple-950/20 border border-purple-500/20 rounded p-3 q-mb-sm'):
                                    with ui.column().classes('gap-0'):
                                        ui.label("Memory Package: Ingress_Faza6").classes('text-sm font-bold text-white')
                                        ui.label("Source: Node 2 (Julka) • 24.5 KB").classes('text-xs text-slate-400')
                                    ui.button("Review & Accept", icon="check_circle", on_click=lambda: ui.notify("CMT Security Gate checklist verified.", type="positive")).props('color=purple size=sm')
                                    
                                with ui.row().classes('items-center justify-between w-full bg-slate-900/60 border border-white/5 rounded p-3'):
                                    with ui.column().classes('gap-0'):
                                        ui.label("Export Package: FailurePatternPack").classes('text-sm font-bold text-slate-400')
                                        ui.label("Target: Node 3 (Piotrek) • Sent").classes('text-xs text-slate-500')
                                    ui.badge("COMPLETED", color="green").classes('text-[10px]')

                    # --- TAB 4: RUNNER (OCI Sandbox) ---
                    with ui.tab_panel(runner_tab).classes('gap-6'):
                        ui.label("Reproducible Experiment Execution (Hive Sandbox)").classes('text-2xl font-bold text-white q-mb-md')
                        
                        with ui.grid(columns=3).classes('w-full gap-6'):
                            # Sandbox List (Left Column)
                            with ui.card().classes('glass-card border border-white/10 text-white q-pa-md col-span-1'):
                                ui.label("OCI Sandboxes").classes('text-sm font-bold text-cyan-400 q-mb-sm')
                                
                                sandboxes = [
                                    {"id": "sbx-t-align-1e5903", "status": "TERMINATED", "detail": "pytest: exit code 0"},
                                    {"id": "sbx-t2-216d0f", "status": "ACTIVE", "detail": "pytest: test_shadow_evaluator.py"},
                                    {"id": "sbx-t-r3-482faf", "status": "ACTIVE", "detail": "dryrun: migration checks"}
                                ]
                                
                                for s in sandboxes:
                                    with ui.card().classes('bg-slate-900/60 border border-white/5 w-full q-pa-xs q-mb-sm'):
                                        with ui.row().classes('w-full justify-between items-center'):
                                            ui.label(s["id"]).classes('text-xs font-bold code-font')
                                            color = "green" if s["status"] == "ACTIVE" else "grey-8"
                                            ui.badge(s["status"], color=color).classes('text-[10px]')
                                        ui.label(s["detail"]).classes('text-xs text-slate-400 q-mt-xs')
                            
                            # Terminal Logs (Right Column, 2/3 width)
                            with ui.card().classes('glass-card border border-white/10 text-white q-pa-md col-span-2'):
                                ui.label("Container Execution Log Stream").classes('text-sm font-bold text-purple-400 q-mb-sm')
                                
                                terminal_mock = (
                                    ui.textarea(
                                        value="[SANDBOX] Starting container sbx-t2-216d0f...\n"
                                              "[SANDBOX] Checking cap-drop=ALL... OK\n"
                                              "[SANDBOX] Checking read-only filesystem... OK\n"
                                              "[SANDBOX] Checking no-new-privileges... OK\n"
                                              "[SANDBOX] Running command: pytest core/test_compliance.py\n"
                                              "================== 21 passed in 0.42s ==================\n"
                                              "[SANDBOX] Audit evidence signed successfully.\n"
                                              "[HIVE] Execution completed with status: SUCCESS\n"
                                    )
                                    .classes('w-full code-font text-green-400 bg-slate-950')
                                    .props('dark borderless readonly rows=10')
                                )
                                
                        # Evidence Packages List
                        ui.label("Verifiable Evidence Packages").classes('text-lg font-bold text-white q-mt-lg q-mb-sm')
                        with ui.card().classes('glass-card border border-white/10 text-white w-full q-pa-md'):
                            with ui.row().classes('w-full justify-between items-center border-b border-white/5 q-pb-xs'):
                                ui.label("Package ID").classes('text-xs font-bold text-slate-400')
                                ui.label("Associated Sandbox").classes('text-xs font-bold text-slate-400')
                                ui.label("SBOM Multihash").classes('text-xs font-bold text-slate-400')
                                ui.label("SAST / Security Verdict").classes('text-xs font-bold text-slate-400')
                            
                            packages = [
                                {"id": "ev-8c6e3e7a", "sbx": "sbx-t-align-1e5903", "hash": "mh:sha256-a1c2e4f5...", "verdict": "SECURE (Trivy: 0, Gitleaks: 0)"},
                                {"id": "ev-05772dc9", "sbx": "sbx-t2-216d0f", "hash": "mh:sha256-f9d2e1a3...", "verdict": "SECURE (Trivy: 0, Gitleaks: 0)"}
                            ]
                            
                            for p in packages:
                                with ui.row().classes('w-full justify-between items-center q-py-sm border-b border-white/5'):
                                    ui.label(p["id"]).classes('text-xs code-font text-purple-300')
                                    ui.label(p["sbx"]).classes('text-xs code-font text-slate-400')
                                    ui.label(p["hash"]).classes('text-xs code-font text-slate-400')
                                    ui.badge(p["verdict"], color="green").classes('text-[10px]')

                    # --- TAB 5: COMPILER (Publication Draft Creator) ---
                    with ui.tab_panel(compiler_tab).classes('gap-6'):
                        ui.label("Publication Draft Creator & Document Compiler").classes('text-2xl font-bold text-white q-mb-md')
                        
                        with ui.row().classes('w-full gap-2 q-mb-md'):
                            ui.label("Select Format:").classes('text-sm font-medium items-center flex')
                            format_select = ui.select(options=["Markdown", "LaTeX"], value="Markdown").classes('w-32').props('dark outlined dense')
                            ui.button("Recompile Draft", icon="refresh", on_click=lambda: refresh_compiler_preview()).props('color=purple size=sm')
                            ui.button("Export ZIP Publication", icon="download", on_click=lambda: ui.notify("ZIP compilation started... Output ready.", type="positive")).props('color=cyan size=sm')
                        
                        with ui.grid(columns=2).classes('w-full gap-6 h-[450px]'):
                            # Left pane: raw draft editor/compiler code view
                            with ui.card().classes('glass-card border border-white/10 text-white q-pa-md h-full overflow-auto'):
                                ui.label("Draft Code Viewer").classes('text-xs font-bold text-slate-400 q-mb-sm')
                                draft_code_display = ui.textarea().classes('w-full h-full code-font text-slate-300 bg-slate-900/60').props('dark borderless readonly')
                            
                            # Right pane: rendered markdown or preview details
                            with ui.card().classes('glass-card border border-white/10 text-white q-pa-md h-full overflow-auto'):
                                ui.label("Compiled Document Preview").classes('text-xs font-bold text-cyan-400 q-mb-sm')
                                draft_html_preview = ui.markdown("Loading preview...")

                        # Citation Manager Mockup
                        ui.label("Epistemic Citation Bibliography").classes('text-lg font-bold text-white q-mt-lg q-mb-sm')
                        with ui.card().classes('glass-card border border-white/10 text-white w-full q-pa-md'):
                            ui.label("Traced DAG dependencies citation mapping:").classes('text-xs text-slate-400 q-mb-sm')
                            ui.label("[1] Hypothesis: 'Data Import: test_observation' derived from Assumption 'Baseline parameters' (Grace Period Cleared).").classes('text-xs code-font text-slate-300')
                            ui.label("[2] Observation: 'Empirical verification' contradicts Hypothesis 'Theoretical model 1' (Watchdog Resolved).").classes('text-xs code-font text-slate-300')

                        async def refresh_compiler_preview():
                            artifacts = await load_all_artifacts()
                            if format_select.value == "Markdown":
                                content = ExportService.to_markdown(artifacts, project)
                                draft_code_display.value = content
                                draft_html_preview.content = content
                            else:
                                content = ExportService.to_latex(artifacts, project)
                                draft_code_display.value = content
                                draft_html_preview.content = "### LaTeX Mode Active\nReview code draft in left panel. LaTeX compilation output is stored as `document.pdf`."
                        
                        await refresh_compiler_preview()

    # --- COOKIE CONSENT BANNER (DREAMSOFT COMPATIBLE) ---
    with ui.card().classes('fixed bottom-4 left-4 right-4 z-[9999] glass-card border border-cyan-500/30 text-white q-pa-md flex flex-row items-center justify-between no-wrap gap-4') as cookie_banner_container:
        with ui.column().classes('gap-1'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('cookie', color='cyan').classes('text-lg')
                ui.label("Cookie Information / Polityka Ciasteczek").classes('text-sm font-bold text-cyan-300')
            ui.label(
                "Ta witryna RAE-CRL używa ciasteczek (cookies) w celach funkcjonalnych (sesje użytkownika, zapisywanie motywu dostępności WCGA) "
                "oraz do zapewnienia zgodności i bezpiecznej integracji z ekosystemem Dreamsoft Factory. Kontynuując korzystanie, zgadzasz się na ich zapis."
            ).classes('text-xs text-slate-300')
        with ui.row().classes('gap-2 no-wrap'):
            ui.button("Ustawienia", on_click=lambda: ui.notify("Funkcjonalne pliki cookies sesji oraz ustawień WCGA są wymagane.")).props('flat dense size=sm color=white')
            ui.button("Akceptuję Wszystkie", on_click=accept_cookies).props('color=cyan size=sm text-color=slate-950')

    # Initial hide of cookie banner if already accepted
    if cookie_accepted:
        cookie_banner_container.set_visibility(False)

# Start NiceGUI
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="RAE-CRL", port=8090, reload=True)
