from nicegui import ui
from apps.crl.core.models import ArtifactType, ArtifactStatus, ArtifactVisibility
from apps.crl.core.database import get_session
from apps.crl.services.storage.sql import SQLRepository
from datetime import datetime

# Helper to run async DB ops
async def run_db(func):
    async for session in get_session():
        repo = SQLRepository(session)
        return await func(repo)

@ui.page('/')
async def main_page():
    # --- STATE ---
    project_id = "default-lab"  # Hardcoded for MVP
    
    # --- LOGIC ---
    async def load_traces():
        async def _get(repo):
            return await repo.list_by_project(project_id, type=ArtifactType.TRACE)
        return await run_db(_get)

    async def add_trace():
        content = trace_input.value
        if not content: return
        
        async def _save(repo):
            from apps.crl.core.models import BaseArtifact
            from datetime import timedelta
            trace = BaseArtifact(
                type=ArtifactType.TRACE,
                title=content[:50] + "..." if len(content) > 50 else content,
                description=content,
                project_id=project_id,
                status=ArtifactStatus.DRAFT,
                visibility=ArtifactVisibility.PRIVATE,
                grace_period_end=datetime.utcnow() + timedelta(hours=24),
                author="me"
            )
            await repo.save(trace)
        
        await run_db(_save)
        trace_input.value = ""
        ui.notify('Trace captured! 🧠', type='positive')
        await refresh_list()

    async def refine_trace(artifact_id):
        # Placeholder for refine logic dialog
        ui.notify(f'Opening refinement for {artifact_id} (Coming soon)', type='info')

    async def trigger_sync():
        from apps.crl.services.sync_service import SyncEngine
        engine = SyncEngine()
        ui.notify('Sync started...', type='ongoing')
        try:
            await engine.run_sync_cycle()
            ui.notify('Sync complete! 🚀', type='positive')
        except Exception as e:
            ui.notify(f'Sync failed: {e}', type='negative')

    # --- UI LAYOUT ---
    with ui.header().classes(replace='row items-center') as header:
        ui.icon('science', size='32px').classes('q-mr-sm')
        ui.label('RAE-CRL Lab Desk').classes('text-h6')
        ui.space()
        ui.button('Sync Now', icon='sync', on_click=trigger_sync).props('flat dense text-color=white')

    with ui.column().classes('w-full q-pa-md items-center'):
        
        # 1. Quick Capture Area
        with ui.card().classes('w-full max-w-3xl q-mb-md'):
            ui.label('Epistemic Quick Capture').classes('text-lg font-bold q-mb-sm')
            with ui.row().classes('w-full no-wrap items-center'):
                trace_input = ui.textarea(placeholder='Dirty thoughts, doubts, quick ideas...').classes('w-full').props('outlined rows=2')
                ui.button(icon='send', on_click=add_trace).props('round color=primary').classes('q-ml-md')

        # 2. Inbox (Traces)
        traces_container = ui.column().classes('w-full max-w-3xl')

    async def refresh_list():
        traces_container.clear()
        traces = await load_traces()
        
        with traces_container:
            if not traces:
                ui.label('Mind clear. No pending traces.').classes('text-grey italic')
            
            for t in traces:
                with ui.card().classes('w-full q-mb-sm hover:shadow-lg transition-shadow'):
                    with ui.row().classes('items-center justify-between no-wrap'):
                        with ui.column().classes('gap-0'):
                            ui.label(t.title).classes('font-medium')
                            ui.label(f"{t.created_at.strftime('%H:%M')} • Grace period active").classes('text-xs text-grey')
                        
                        with ui.row():
                            ui.button(icon='edit', on_click=lambda id=t.id: refine_trace(id)).props('flat round dense color=primary').tooltip('Refine to Artifact')
                            ui.button(icon='delete', on_click=lambda: ui.notify('Delete not impl yet')).props('flat round dense color=negative')

    await refresh_list()

# Start
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="RAE-CRL", port=8080, reload=True)
