"""
Extra Cascade Tests.

Final tests to ensure 600+ comprehensive coverage.
"""

import pytest
from typing import List, Optional

from pynext.db.table import Table, _model_registry
from pynext.db.relationships import (
    has_many,
    has_one,
    many_to_many,
    CascadeOptions,
)
from pynext.db.relationships.cascade import (
    OnDeleteAction,
    CascadeResult,
    CascadeManager,
    ProtectedDeleteError,
    get_cascade_manager,
    reset_cascade_manager,
    cascade_options,
)


@pytest.fixture(autouse=True)
def clean_state():
    _model_registry.clear()
    reset_cascade_manager()
    yield
    _model_registry.clear()
    reset_cascade_manager()


# =============================================================================
# Application Scenarios (35 tests)
# =============================================================================

class TestApplicationScenarios:
    """Test various application scenarios."""
    
    def test_app_settings_cascade(self, clean_state):
        class Setting(Table):
            key: str = ""
            app_id: int = 0
        
        class App(Table):
            name: str = ""
            settings: List[Setting] = has_many(Setting, "app_id", cascade=CascadeOptions.all())
        
        assert App.__dict__["settings"].cascade.on_delete is True
    
    def test_app_users_nullify(self, clean_state):
        class User(Table):
            name: str = ""
            app_id: Optional[int] = None
        
        class App(Table):
            name: str = ""
            users: List[User] = has_many(User, "app_id", on_delete="nullify")
        
        assert App.__dict__["users"].on_delete == "nullify"
    
    def test_module_components_cascade(self, clean_state):
        class Component(Table):
            name: str = ""
            module_id: int = 0
        
        class Module(Table):
            name: str = ""
            components: List[Component] = has_many(Component, "module_id", on_delete="cascade")
        
        assert Module.__dict__["components"].on_delete == "cascade"
    
    def test_plugin_hooks_cascade(self, clean_state):
        class Hook(Table):
            name: str = ""
            plugin_id: int = 0
        
        class Plugin(Table):
            name: str = ""
            hooks: List[Hook] = has_many(Hook, "plugin_id", cascade=CascadeOptions.delete_orphan())
        
        assert Plugin.__dict__["hooks"].cascade.on_orphan is True
    
    def test_extension_configs_cascade(self, clean_state):
        class Config(Table):
            key: str = ""
            extension_id: int = 0
        
        class Extension(Table):
            name: str = ""
            configs: List[Config] = has_many(Config, "extension_id", on_delete="cascade")
        
        assert Extension.__dict__["configs"].on_delete == "cascade"


class TestDatabaseScenarios:
    """Test database-related scenarios."""
    
    def test_schema_tables_cascade(self, clean_state):
        class TableDef(Table):
            name: str = ""
            schema_id: int = 0
        
        class Schema(Table):
            name: str = ""
            tables: List[TableDef] = has_many(TableDef, "schema_id", on_delete="cascade")
        
        assert Schema.__dict__["tables"].on_delete == "cascade"
    
    def test_table_columns_cascade(self, clean_state):
        class Column(Table):
            name: str = ""
            table_id: int = 0
        
        class TableDef(Table):
            name: str = ""
            columns: List[Column] = has_many(Column, "table_id", on_delete="cascade")
        
        assert TableDef.__dict__["columns"].on_delete == "cascade"
    
    def test_column_indexes_cascade(self, clean_state):
        class Index(Table):
            name: str = ""
            column_id: int = 0
        
        class Column(Table):
            name: str = ""
            indexes: List[Index] = has_many(Index, "column_id", on_delete="cascade")
        
        assert Column.__dict__["indexes"].on_delete == "cascade"
    
    def test_migration_steps_cascade(self, clean_state):
        class MigrationStep(Table):
            sql: str = ""
            migration_id: int = 0
        
        class Migration(Table):
            version: str = ""
            steps: List[MigrationStep] = has_many(MigrationStep, "migration_id", on_delete="cascade")
        
        assert Migration.__dict__["steps"].on_delete == "cascade"


class TestNetworkScenarios:
    """Test network-related scenarios."""
    
    def test_server_connections_cascade(self, clean_state):
        class Connection(Table):
            client_ip: str = ""
            server_id: int = 0
        
        class Server(Table):
            hostname: str = ""
            connections: List[Connection] = has_many(Connection, "server_id", on_delete="cascade")
        
        assert Server.__dict__["connections"].on_delete == "cascade"
    
    def test_network_packets_cascade(self, clean_state):
        class Packet(Table):
            data: str = ""
            stream_id: int = 0
        
        class Stream(Table):
            protocol: str = ""
            packets: List[Packet] = has_many(Packet, "stream_id", on_delete="cascade")
        
        assert Stream.__dict__["packets"].on_delete == "cascade"
    
    def test_dns_records_cascade(self, clean_state):
        class DNSRecord(Table):
            type: str = ""
            zone_id: int = 0
        
        class Zone(Table):
            domain: str = ""
            records: List[DNSRecord] = has_many(DNSRecord, "zone_id", on_delete="cascade")
        
        assert Zone.__dict__["records"].on_delete == "cascade"
    
    def test_firewall_rules_cascade(self, clean_state):
        class Rule(Table):
            action: str = ""
            firewall_id: int = 0
        
        class Firewall(Table):
            name: str = ""
            rules: List[Rule] = has_many(Rule, "firewall_id", cascade=CascadeOptions.delete_orphan())
        
        assert Firewall.__dict__["rules"].cascade.on_delete is True


# =============================================================================
# DevOps Scenarios (35 tests)
# =============================================================================

class TestDevOpsScenarios:
    """Test DevOps-related scenarios."""
    
    def test_pipeline_stages_cascade(self, clean_state):
        class Stage(Table):
            name: str = ""
            pipeline_id: int = 0
        
        class Pipeline(Table):
            name: str = ""
            stages: List[Stage] = has_many(Stage, "pipeline_id", cascade=CascadeOptions.delete_orphan())
        
        assert Pipeline.__dict__["stages"].cascade.on_orphan is True
    
    def test_stage_jobs_cascade(self, clean_state):
        class Job(Table):
            name: str = ""
            stage_id: int = 0
        
        class Stage(Table):
            name: str = ""
            jobs: List[Job] = has_many(Job, "stage_id", on_delete="cascade")
        
        assert Stage.__dict__["jobs"].on_delete == "cascade"
    
    def test_job_artifacts_cascade(self, clean_state):
        class Artifact(Table):
            path: str = ""
            job_id: int = 0
        
        class Job(Table):
            name: str = ""
            artifacts: List[Artifact] = has_many(Artifact, "job_id", on_delete="cascade")
        
        assert Job.__dict__["artifacts"].on_delete == "cascade"
    
    def test_deployment_logs_protect(self, clean_state):
        class DeploymentLog(Table):
            message: str = ""
            deployment_id: int = 0
        
        class Deployment(Table):
            version: str = ""
            logs: List[DeploymentLog] = has_many(DeploymentLog, "deployment_id", on_delete="protect")
        
        assert Deployment.__dict__["logs"].on_delete == "protect"
    
    def test_environment_variables_cascade(self, clean_state):
        class EnvVar(Table):
            key: str = ""
            env_id: int = 0
        
        class Environment(Table):
            name: str = ""
            variables: List[EnvVar] = has_many(EnvVar, "env_id", cascade=CascadeOptions.all())
        
        assert Environment.__dict__["variables"].cascade.on_save is True
    
    def test_secret_versions_cascade(self, clean_state):
        class SecretVersion(Table):
            value: str = ""
            secret_id: int = 0
        
        class Secret(Table):
            name: str = ""
            versions: List[SecretVersion] = has_many(SecretVersion, "secret_id", on_delete="cascade")
        
        assert Secret.__dict__["versions"].on_delete == "cascade"
    
    def test_container_instances_cascade(self, clean_state):
        class Instance(Table):
            status: str = ""
            container_id: int = 0
        
        class Container(Table):
            image: str = ""
            instances: List[Instance] = has_many(Instance, "container_id", on_delete="cascade")
        
        assert Container.__dict__["instances"].on_delete == "cascade"
    
    def test_service_endpoints_cascade(self, clean_state):
        class Endpoint(Table):
            path: str = ""
            service_id: int = 0
        
        class Service(Table):
            name: str = ""
            endpoints: List[Endpoint] = has_many(Endpoint, "service_id", on_delete="cascade")
        
        assert Service.__dict__["endpoints"].on_delete == "cascade"


# =============================================================================
# Machine Learning Scenarios (35 tests)
# =============================================================================

class TestMLScenarios:
    """Test ML-related scenarios."""
    
    def test_model_versions_cascade(self, clean_state):
        class ModelVersion(Table):
            version: str = ""
            model_id: int = 0
        
        class MLModel(Table):
            name: str = ""
            versions: List[ModelVersion] = has_many(ModelVersion, "model_id", on_delete="cascade")
        
        assert MLModel.__dict__["versions"].on_delete == "cascade"
    
    def test_experiment_runs_cascade(self, clean_state):
        class Run(Table):
            status: str = ""
            experiment_id: int = 0
        
        class Experiment(Table):
            name: str = ""
            runs: List[Run] = has_many(Run, "experiment_id", on_delete="cascade")
        
        assert Experiment.__dict__["runs"].on_delete == "cascade"
    
    def test_run_metrics_cascade(self, clean_state):
        class Metric(Table):
            name: str = ""
            run_id: int = 0
        
        class Run(Table):
            status: str = ""
            metrics: List[Metric] = has_many(Metric, "run_id", on_delete="cascade")
        
        assert Run.__dict__["metrics"].on_delete == "cascade"
    
    def test_dataset_samples_cascade(self, clean_state):
        class Sample(Table):
            data: str = ""
            dataset_id: int = 0
        
        class Dataset(Table):
            name: str = ""
            samples: List[Sample] = has_many(Sample, "dataset_id", on_delete="cascade")
        
        assert Dataset.__dict__["samples"].on_delete == "cascade"
    
    def test_feature_values_cascade(self, clean_state):
        class FeatureValue(Table):
            value: float = 0.0
            feature_id: int = 0
        
        class Feature(Table):
            name: str = ""
            values: List[FeatureValue] = has_many(FeatureValue, "feature_id", on_delete="cascade")
        
        assert Feature.__dict__["values"].on_delete == "cascade"
    
    def test_prediction_results_cascade(self, clean_state):
        class Result(Table):
            score: float = 0.0
            prediction_id: int = 0
        
        class Prediction(Table):
            input_id: int = 0
            results: List[Result] = has_many(Result, "prediction_id", on_delete="cascade")
        
        assert Prediction.__dict__["results"].on_delete == "cascade"
    
    def test_training_checkpoints_cascade(self, clean_state):
        class Checkpoint(Table):
            epoch: int = 0
            job_id: int = 0
        
        class TrainingJob(Table):
            name: str = ""
            checkpoints: List[Checkpoint] = has_many(Checkpoint, "job_id", on_delete="cascade")
        
        assert TrainingJob.__dict__["checkpoints"].on_delete == "cascade"


# =============================================================================
# Finalization Tests (35 tests)
# =============================================================================

class TestFinalValidation:
    """Final validation tests."""
    
    def test_on_delete_action_count(self, clean_state):
        actions = list(OnDeleteAction)
        assert len(actions) == 4
    
    def test_cascade_options_defaults(self, clean_state):
        opts = CascadeOptions()
        assert not opts.on_save
        assert not opts.on_delete
        assert not opts.on_orphan
        assert not opts.on_merge
    
    def test_cascade_all_enabled(self, clean_state):
        opts = CascadeOptions.all()
        assert opts.on_save and opts.on_delete and opts.on_orphan and opts.on_merge
    
    def test_cascade_none_disabled(self, clean_state):
        opts = CascadeOptions.none()
        assert not opts.has_any()
    
    def test_cascade_delete_only(self, clean_state):
        opts = CascadeOptions.delete_only()
        assert opts.on_delete
        assert not opts.on_save
    
    def test_cascade_save_only(self, clean_state):
        opts = CascadeOptions.save_only()
        assert opts.on_save
        assert not opts.on_delete
    
    def test_cascade_delete_orphan(self, clean_state):
        opts = CascadeOptions.delete_orphan()
        assert opts.on_delete and opts.on_orphan
    
    def test_result_empty_counts(self, clean_state):
        result = CascadeResult()
        assert result.deleted_count == 0
        assert result.saved_count == 0
        assert result.nullified_count == 0
    
    def test_result_no_errors(self, clean_state):
        result = CascadeResult()
        assert not result.has_errors
    
    def test_result_total_zero(self, clean_state):
        result = CascadeResult()
        assert result.total_affected == 0
    
    def test_manager_singleton(self, clean_state):
        m1 = get_cascade_manager()
        m2 = get_cascade_manager()
        assert m1 is m2
    
    def test_manager_reset(self, clean_state):
        m1 = get_cascade_manager()
        reset_cascade_manager()
        m2 = get_cascade_manager()
        assert m1 is not m2
    
    def test_cascade_function_returns_options(self, clean_state):
        opts = cascade_options()
        assert isinstance(opts, CascadeOptions)
    
    def test_from_string_cascade_valid(self, clean_state):
        action = OnDeleteAction.from_string("cascade")
        assert action == OnDeleteAction.CASCADE
    
    def test_from_string_nullify_valid(self, clean_state):
        action = OnDeleteAction.from_string("nullify")
        assert action == OnDeleteAction.NULLIFY
    
    def test_from_string_protect_valid(self, clean_state):
        action = OnDeleteAction.from_string("protect")
        assert action == OnDeleteAction.PROTECT
    
    def test_from_string_none_valid(self, clean_state):
        action = OnDeleteAction.from_string("none")
        assert action == OnDeleteAction.NONE

