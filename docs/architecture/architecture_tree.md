scientific-workflow-runtime/
├─ .github/
│  ├─ ISSUE_TEMPLATE/
│  │  ├─ bug_report.md
│  │  ├─ feature_request.md
│  │  ├─ design_decision.md
│  │  ├─ plugin_request.md
│  │  └─ workflow_demo.md
│  ├─ workflows/
│  │  ├─ ci.yml
│  │  ├─ lint.yml
│  │  ├─ docs.yml
│  │  └─ release.yml
│  ├─ PULL_REQUEST_TEMPLATE.md
│  └─ CODEOWNERS
│
├─ apps/
│  ├─ web/
│  │  ├─ README.md
│  │  ├─ package.json
│  │  ├─ tsconfig.json
│  │  ├─ vite.config.ts
│  │  ├─ public/
│  │  └─ src/
│  │     ├─ main.tsx
│  │     ├─ App.tsx
│  │     ├─ pages/
│  │     │  ├─ WorkflowEditorPage.tsx
│  │     │  ├─ RunMonitorPage.tsx
│  │     │  ├─ ObjectExplorerPage.tsx
│  │     │  ├─ ArtifactViewerPage.tsx
│  │     │  └─ SettingsPage.tsx
│  │     ├─ components/
│  │     │  ├─ graph/
│  │     │  │  ├─ WorkflowCanvas.tsx
│  │     │  │  ├─ BlockNode.tsx
│  │     │  │  ├─ PortHandle.tsx
│  │     │  │  └─ EdgeLabel.tsx
│  │     │  ├─ inspector/
│  │     │  │  ├─ BlockInspector.tsx
│  │     │  │  ├─ ParamForm.tsx
│  │     │  │  └─ PortSchemaViewer.tsx
│  │     │  ├─ run/
│  │     │  │  ├─ RunStatusPanel.tsx
│  │     │  │  ├─ BlockRunCard.tsx
│  │     │  │  ├─ LogViewer.tsx
│  │     │  │  └─ ManualTaskQueue.tsx
│  │     │  ├─ objects/
│  │     │  │  ├─ ObjectCard.tsx
│  │     │  │  ├─ ObjectMetadataPanel.tsx
│  │     │  │  └─ LineageView.tsx
│  │     │  ├─ preview/
│  │     │  │  ├─ ImagePreview.tsx
│  │     │  │  ├─ TablePreview.tsx
│  │     │  │  ├─ TextPreview.tsx
│  │     │  │  └─ ArtifactPreview.tsx
│  │     │  └─ common/
│  │     ├─ hooks/
│  │     ├─ api/
│  │     ├─ state/
│  │     ├─ schemas/
│  │     ├─ styles/
│  │     └─ utils/
│  │
│  ├─ api/
│  │  ├─ README.md
│  │  ├─ pyproject.toml
│  │  ├─ app/
│  │  │  ├─ main.py
│  │  │  ├─ dependencies.py
│  │  │  ├─ config.py
│  │  │  ├─ routers/
│  │  │  │  ├─ health.py
│  │  │  │  ├─ workflows.py
│  │  │  │  ├─ runs.py
│  │  │  │  ├─ blocks.py
│  │  │  │  ├─ objects.py
│  │  │  │  ├─ artifacts.py
│  │  │  │  ├─ plugins.py
│  │  │  │  └─ ai.py
│  │  │  ├─ services/
│  │  │  ├─ schemas/
│  │  │  └─ middleware/
│  │  └─ tests/
│  │
│  ├─ worker/
│  │  ├─ README.md
│  │  ├─ pyproject.toml
│  │  └─ worker/
│  │     ├─ main.py
│  │     ├─ job_runner.py
│  │     ├─ task_dispatcher.py
│  │     ├─ external_app_runner.py
│  │     ├─ interactive_runner.py
│  │     └─ environment_manager.py
│  │
│  ├─ cli/
│  │  ├─ README.md
│  │  ├─ pyproject.toml
│  │  └─ cli/
│  │     ├─ main.py
│  │     ├─ commands/
│  │     │  ├─ init.py
│  │     │  ├─ validate.py
│  │     │  ├─ run.py
│  │     │  ├─ plugin.py
│  │     │  └─ doctor.py
│  │     └─ utils/
│  │
│  └─ desktop/
│     ├─ README.md
│     ├─ src-tauri/
│     └─ shell/
│
├─ packages/
│  ├─ core/
│  │  ├─ README.md
│  │  ├─ pyproject.toml
│  │  └─ core/
│  │     ├─ __init__.py
│  │     ├─ version.py
│  │     ├─ constants.py
│  │     ├─ exceptions.py
│  │     ├─ types/
│  │     │  ├─ __init__.py
│  │     │  ├─ data_object.py
│  │     │  ├─ primitive_types.py
│  │     │  ├─ capabilities.py
│  │     │  └─ metadata.py
│  │     ├─ graph/
│  │     │  ├─ __init__.py
│  │     │  ├─ workflow.py
│  │     │  ├─ node.py
│  │     │  ├─ edge.py
│  │     │  ├─ ports.py
│  │     │  ├─ validation.py
│  │     │  └─ serialization.py
│  │     ├─ blocks/
│  │     │  ├─ __init__.py
│  │     │  ├─ base.py
│  │     │  ├─ spec.py
│  │     │  ├─ params.py
│  │     │  ├─ registry.py
│  │     │  └─ categories.py
│  │     ├─ runs/
│  │     │  ├─ __init__.py
│  │     │  ├─ state_machine.py
│  │     │  ├─ run_record.py
│  │     │  ├─ events.py
│  │     │  └─ checkpoints.py
│  │     ├─ lineage/
│  │     │  ├─ __init__.py
│  │     │  ├─ provenance.py
│  │     │  ├─ audit_log.py
│  │     │  └─ signatures.py
│  │     └─ utils/
│  │
│  ├─ runtime/
│  │  ├─ README.md
│  │  ├─ pyproject.toml
│  │  └─ runtime/
│  │     ├─ __init__.py
│  │     ├─ executor.py
│  │     ├─ local_executor.py
│  │     ├─ parallel_executor.py
│  │     ├─ interactive_executor.py
│  │     ├─ scheduler.py
│  │     ├─ cache.py
│  │     ├─ retries.py
│  │     ├─ resource_manager.py
│  │     └─ event_bus.py
│  │
│  ├─ storage/
│  │  ├─ README.md
│  │  ├─ pyproject.toml
│  │  └─ storage/
│  │     ├─ __init__.py
│  │     ├─ object_store.py
│  │     ├─ refs.py
│  │     ├─ array_store/
│  │     │  ├─ zarr_backend.py
│  │     │  └─ preview_builder.py
│  │     ├─ table_store/
│  │     │  ├─ parquet_backend.py
│  │     │  └─ query_adapter.py
│  │     ├─ artifact_store/
│  │     │  ├─ file_backend.py
│  │     │  └─ manifest.py
│  │     ├─ metadata_store/
│  │     │  ├─ models.py
│  │     │  ├─ repository.py
│  │     │  └─ migrations/
│  │     └─ cache_store/
│  │
│  ├─ sdk/
│  │  ├─ README.md
│  │  ├─ pyproject.toml
│  │  └─ sdk/
│  │     ├─ __init__.py
│  │     ├─ block_sdk.py
│  │     ├─ datatype_sdk.py
│  │     ├─ reader_sdk.py
│  │     ├─ writer_sdk.py
│  │     ├─ external_app_sdk.py
│  │     ├─ ai_sdk.py
│  │     └─ templates/
│  │        ├─ block_template.py
│  │        ├─ datatype_template.py
│  │        └─ plugin_template.py
│  │
│  ├─ plugin_host/
│  │  ├─ README.md
│  │  ├─ pyproject.toml
│  │  └─ plugin_host/
│  │     ├─ __init__.py
│  │     ├─ manager.py
│  │     ├─ discovery.py
│  │     ├─ hooks.py
│  │     ├─ compatibility.py
│  │     └─ sandbox.py
│  │
│  ├─ plugins_builtin/
│  │  ├─ README.md
│  │  ├─ pyproject.toml
│  │  └─ plugins_builtin/
│  │     ├─ __init__.py
│  │     ├─ loaders/
│  │     ├─ transforms/
│  │     ├─ control/
│  │     ├─ export/
│  │     └─ manual/
│  │
│  ├─ plugins_python/
│  │  ├─ README.md
│  │  └─ plugins_python/
│  │     ├─ python_block.py
│  │     ├─ env_spec.py
│  │     └─ code_snapshot.py
│  │
│  ├─ plugins_r/
│  │  ├─ README.md
│  │  └─ plugins_r/
│  │     ├─ r_block.py
│  │     ├─ env_spec.py
│  │     └─ script_runner.py
│  │
│  ├─ plugins_shell/
│  │  ├─ README.md
│  │  └─ plugins_shell/
│  │     ├─ shell_block.py
│  │     └─ process_runner.py
│  │
│  ├─ plugins_external_apps/
│  │  ├─ README.md
│  │  └─ plugins_external_apps/
│  │     ├─ __init__.py
│  │     ├─ base_adapter.py
│  │     ├─ open_and_wait.py
│  │     ├─ connected_session.py
│  │     ├─ file_watchers.py
│  │     ├─ elmaven/
│  │     │  ├─ adapter.py
│  │     │  ├─ io_contract.md
│  │     │  └─ README.md
│  │     ├─ fiji/
│  │     │  ├─ adapter.py
│  │     │  └─ README.md
│  │     └─ napari/
│  │        ├─ adapter.py
│  │        └─ README.md
│  │
│  ├─ plugins_imaging/
│  │  ├─ README.md
│  │  └─ plugins_imaging/
│  │     ├─ io/
│  │     ├─ segmentation/
│  │     ├─ registration/
│  │     ├─ masks/
│  │     └─ features/
│  │
│  ├─ plugins_spectra/
│  │  ├─ README.md
│  │  └─ plugins_spectra/
│  │     ├─ io/
│  │     ├─ preprocess/
│  │     ├─ peak_picking/
│  │     ├─ baseline/
│  │     └─ fitting/
│  │
│  ├─ plugins_omics/
│  │  ├─ README.md
│  │  └─ plugins_omics/
│  │     ├─ transcriptomics/
│  │     ├─ metabolomics/
│  │     ├─ lcms/
│  │     └─ spatial/
│  │
│  ├─ plugins_multimodal/
│  │  ├─ README.md
│  │  └─ plugins_multimodal/
│  │     ├─ join/
│  │     ├─ align/
│  │     ├─ map_features/
│  │     └─ fusion/
│  │
│  └─ ai/
│     ├─ README.md
│     ├─ pyproject.toml
│     └─ ai/
│        ├─ __init__.py
│        ├─ graph_compiler.py
│        ├─ block_recommender.py
│        ├─ param_suggester.py
│        ├─ plugin_scaffolder.py
│        ├─ optimization/
│        ├─ prompt_templates/
│        └─ guards/
│
├─ schemas/
│  ├─ README.md
│  ├─ graph/
│  │  ├─ workflow.schema.json
│  │  ├─ node.schema.json
│  │  ├─ edge.schema.json
│  │  └─ port.schema.json
│  ├─ blocks/
│  │  ├─ block_spec.schema.json
│  │  ├─ params.schema.json
│  │  └─ execution_modes.schema.json
│  ├─ objects/
│  │  ├─ data_object.schema.json
│  │  ├─ primitive_types.schema.json
│  │  └─ metadata.schema.json
│  ├─ runs/
│  │  ├─ run_record.schema.json
│  │  ├─ state_transition.schema.json
│  │  └─ audit_event.schema.json
│  └─ plugins/
│     ├─ plugin_manifest.schema.json
│     └─ compatibility.schema.json
│
├─ docs/
│  ├─ README.md
│  ├─ project/
│  │  ├─ project_charter.md
│  │  ├─ product_scope.md
│  │  ├─ glossary.md
│  │  ├─ non_goals.md
│  │  └─ stakeholders.md
│  ├─ architecture/
│  │  ├─ overview.md
│  │  ├─ object_model.md
│  │  ├─ block_protocol.md
│  │  ├─ runtime_state_machine.md
│  │  ├─ storage_strategy.md
│  │  ├─ plugin_architecture.md
│  │  ├─ external_app_protocol.md
│  │  ├─ ai_orchestration.md
│  │  └─ security_model.md
│  ├─ adr/
│  │  ├─ 0000-template.md
│  │  └─ README.md
│  ├─ specs/
│  │  ├─ SPEC_TEMPLATE.md
│  │  ├─ v0.1-core-runtime.md
│  │  ├─ v0.2-storage.md
│  │  ├─ v0.3-batch-and-interactive.md
│  │  ├─ v0.4-external-apps.md
│  │  └─ v0.5-web-ui.md
│  ├─ roadmap/
│  │  ├─ ROADMAP.md
│  │  ├─ milestones.md
│  │  └─ release_strategy.md
│  ├─ workflows/
│  │  ├─ demo-lcms-raman-if-srs.md
│  │  ├─ demo-spatial-omics.md
│  │  └─ workflow_json_examples/
│  ├─ operations/
│  │  ├─ dev_setup.md
│  │  ├─ ci_cd.md
│  │  ├─ branching_strategy.md
│  │  ├─ release_checklist.md
│  │  ├─ incident_response.md
│  │  └─ support_triage.md
│  └─ contributing/
│     ├─ CONTRIBUTING.md
│     ├─ coding_standards.md
│     ├─ testing_strategy.md
│     ├─ plugin_dev_guide.md
│     └─ review_guide.md
│
├─ examples/
│  ├─ README.md
│  ├─ workflows/
│  │  ├─ lcms_raman_if_srs/
│  │  ├─ batch_spectra_processing/
│  │  ├─ image_segmentation_manual_review/
│  │  └─ external_app_pause_resume/
│  ├─ sample_data/
│  └─ notebooks/
│
├─ tests/
│  ├─ README.md
│  ├─ unit/
│  │  ├─ core/
│  │  ├─ runtime/
│  │  ├─ storage/
│  │  ├─ sdk/
│  │  └─ plugins/
│  ├─ integration/
│  │  ├─ workflow_runs/
│  │  ├─ storage_backends/
│  │  ├─ external_apps/
│  │  └─ api/
│  ├─ e2e/
│  │  ├─ web/
│  │  └─ demo_workflows/
│  ├─ fixtures/
│  │  ├─ objects/
│  │  ├─ workflows/
│  │  └─ sample_outputs/
│  └─ golden/
│     ├─ lineage/
│     ├─ artifacts/
│     └─ previews/
│
├─ scripts/
│  ├─ bootstrap.sh
│  ├─ bootstrap.ps1
│  ├─ dev.sh
│  ├─ lint.sh
│  ├─ test.sh
│  ├─ build_docs.sh
│  ├─ release.sh
│  └─ scaffold_plugin.py
│
├─ configs/
│  ├─ pyproject.toml
│  ├─ .pre-commit-config.yaml
│  ├─ .editorconfig
│  ├─ ruff.toml
│  ├─ pytest.ini
│  ├─ mypy.ini
│  └─ env/
│     ├─ local.env.example
│     ├─ dev.env.example
│     └─ prod.env.example
│
├─ infra/
│  ├─ docker/
│  │  ├─ api.Dockerfile
│  │  ├─ worker.Dockerfile
│  │  ├─ web.Dockerfile
│  │  └─ base-python.Dockerfile
│  ├─ compose/
│  │  ├─ docker-compose.dev.yml
│  │  └─ docker-compose.test.yml
│  └─ deployment/
│     ├─ local/
│     └─ cloud/
│
├─ data/
│  ├─ .gitkeep
│  ├─ local/
│  ├─ cache/
│  ├─ artifacts/
│  └─ previews/
│
├─ CHANGELOG.md
├─ CODE_OF_CONDUCT.md
├─ CONTRIBUTING.md
├─ LICENSE
├─ README.md
└─ SECURITY.md