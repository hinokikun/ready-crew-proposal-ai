from __future__ import annotations

from app.database.connection import _id_column


def _schema_statements() -> list[str]:
    id_column = _id_column()
    return [
        f"""
        CREATE TABLE IF NOT EXISTS organizations (
            id {id_column},
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS workspaces (
            id {id_column},
            organization_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(organization_id, slug),
            FOREIGN KEY(organization_id) REFERENCES organizations(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS organization_memberships (
            id {id_column},
            user_id INTEGER NOT NULL,
            organization_id INTEGER NOT NULL,
            workspace_id INTEGER NOT NULL,
            membership_role TEXT NOT NULL DEFAULT 'member',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, organization_id, workspace_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(organization_id) REFERENCES organizations(id),
            FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_memberships_user ON organization_memberships(user_id, organization_id, workspace_id)",
        f"""
        CREATE TABLE IF NOT EXISTS users (
            id {id_column},
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'manager', 'member', 'viewer')),
            current_organization_id INTEGER NOT NULL DEFAULT 1,
            current_workspace_id INTEGER NOT NULL DEFAULT 1,
            is_active INTEGER NOT NULL DEFAULT 1,
            auth_version INTEGER NOT NULL DEFAULT 1,
            pilot_enabled INTEGER NOT NULL DEFAULT 0,
            pilot_started_at TEXT,
            pilot_last_used_at TEXT,
            pilot_completed INTEGER NOT NULL DEFAULT 0,
            pilot_note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS customers (
            id {id_column},
            company_name TEXT NOT NULL,
            industry TEXT NOT NULL DEFAULT '',
            contact_person TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS projects (
            id {id_column},
            customer_id INTEGER,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            win_probability INTEGER NOT NULL DEFAULT 0,
            summary TEXT NOT NULL DEFAULT '',
            next_action TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS project_lifecycle_events (
            id {id_column},
            project_id INTEGER NOT NULL,
            user_id INTEGER,
            event_type TEXT NOT NULL DEFAULT '',
            from_status TEXT NOT NULL DEFAULT '',
            to_status TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_project_lifecycle_events_project ON project_lifecycle_events(project_id, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS project_outcomes (
            id {id_column},
            project_id INTEGER NOT NULL UNIQUE,
            outcome TEXT NOT NULL DEFAULT '',
            lost_reason TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS project_handoffs (
            id {id_column},
            project_id INTEGER NOT NULL UNIQUE,
            handoff_text TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS project_retrospectives (
            id {id_column},
            project_id INTEGER NOT NULL UNIQUE,
            success_factors TEXT NOT NULL DEFAULT '',
            improvements TEXT NOT NULL DEFAULT '',
            next_learnings TEXT NOT NULL DEFAULT '',
            knowledge_candidate_id INTEGER,
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS proposal_histories (
            id {id_column},
            user_id INTEGER,
            customer_id INTEGER,
            project_id INTEGER,
            feature_name TEXT NOT NULL,
            input_length INTEGER NOT NULL DEFAULT 0,
            output_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'success',
            error_type TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS meeting_memos (
            id {id_column},
            user_id INTEGER,
            project_id INTEGER,
            summary TEXT NOT NULL DEFAULT '',
            next_action TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id {id_column},
            user_id INTEGER,
            feature_name TEXT NOT NULL,
            input_length INTEGER NOT NULL DEFAULT 0,
            output_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'success',
            error_type TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id {id_column},
            user_id INTEGER,
            event_type TEXT NOT NULL,
            target_type TEXT NOT NULL DEFAULT '',
            target_id TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'success',
            metadata TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS pilot_events (
            id {id_column},
            user_id INTEGER,
            event_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'success',
            duration_ms INTEGER NOT NULL DEFAULT 0,
            metadata TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_pilot_events_user ON pilot_events(user_id, event_type, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS pilot_issues (
            id {id_column},
            issue_id TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL DEFAULT 'other',
            severity TEXT NOT NULL DEFAULT 'medium',
            title TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            reproduction_steps TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'reported',
            reported_by INTEGER,
            assigned_to TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            resolved_at TEXT,
            resolution_note TEXT NOT NULL DEFAULT '',
            source_feedback_id INTEGER,
            FOREIGN KEY(reported_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_pilot_issues_status ON pilot_issues(status, severity, updated_at)",
        f"""
        CREATE TABLE IF NOT EXISTS app_runtime_settings (
            key TEXT NOT NULL PRIMARY KEY,
            value TEXT NOT NULL DEFAULT '',
            updated_by INTEGER,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            note TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(updated_by) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS ai_notifications (
            id {id_column},
            notification_key TEXT NOT NULL UNIQUE,
            user_id INTEGER,
            project_id INTEGER,
            agent_name TEXT NOT NULL DEFAULT '',
            priority TEXT NOT NULL DEFAULT '中',
            title TEXT NOT NULL DEFAULT '',
            message TEXT NOT NULL DEFAULT '',
            recommended_action TEXT NOT NULL DEFAULT '',
            source_type TEXT NOT NULL DEFAULT '',
            source_id TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'unread',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            read_at TEXT,
            archived_at TEXT,
            actioned_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_ai_notifications_user_status ON ai_notifications(user_id, status, priority, updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_ai_notifications_project ON ai_notifications(project_id, source_type)",
        f"""
        CREATE TABLE IF NOT EXISTS integration_settings (
            id {id_column},
            provider TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT '未接続',
            display_name TEXT NOT NULL DEFAULT '',
            enabled INTEGER NOT NULL DEFAULT 0,
            allowed_roles TEXT NOT NULL DEFAULT 'admin,manager,member',
            requires_admin_approval INTEGER NOT NULL DEFAULT 1,
            data_retention_days INTEGER NOT NULL DEFAULT 90,
            last_checked_at TEXT,
            last_security_review_at TEXT,
            error_message TEXT NOT NULL DEFAULT '',
            security_note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_integration_settings_status ON integration_settings(status, enabled, updated_at)",
        f"""
        CREATE TABLE IF NOT EXISTS external_intake_items (
            id {id_column},
            source_provider TEXT NOT NULL,
            source_type TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            received_at TEXT NOT NULL DEFAULT '',
            metadata TEXT NOT NULL DEFAULT '',
            candidate_status TEXT NOT NULL DEFAULT 'pending_review',
            security_flags TEXT NOT NULL DEFAULT '',
            reviewed_by INTEGER,
            reviewed_at TEXT,
            review_comment TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            project_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(id),
            FOREIGN KEY(reviewed_by) REFERENCES users(id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_external_intake_provider ON external_intake_items(source_provider, candidate_status, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_external_intake_user ON external_intake_items(created_by, candidate_status, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS dry_run_logs (
            id {id_column},
            provider TEXT NOT NULL,
            template_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'success',
            created_item_id INTEGER,
            result_summary TEXT NOT NULL DEFAULT '',
            security_flags_count INTEGER NOT NULL DEFAULT 0,
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_item_id) REFERENCES external_intake_items(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_dry_run_logs_provider ON dry_run_logs(provider, status, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS action_queue (
            id {id_column},
            project_id INTEGER,
            action_type TEXT NOT NULL,
            agent TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            priority INTEGER NOT NULL DEFAULT 50,
            reason TEXT NOT NULL DEFAULT '',
            result_summary TEXT NOT NULL DEFAULT '',
            error_type TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            started_at TEXT,
            completed_at TEXT,
            retry_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_action_queue_status_priority ON action_queue(status, priority, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_action_queue_project ON action_queue(project_id, status, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS learning_runs (
            id {id_column},
            triggered_by INTEGER,
            status TEXT NOT NULL DEFAULT 'success',
            analyzed_items_count INTEGER NOT NULL DEFAULT 0,
            metrics_summary TEXT NOT NULL DEFAULT '',
            release_candidate_version TEXT NOT NULL DEFAULT '13.6候補',
            release_candidate_summary TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(triggered_by) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS learning_improvements (
            id {id_column},
            run_id INTEGER,
            improvement_type TEXT NOT NULL DEFAULT 'prompt',
            agent TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT '',
            current_version TEXT NOT NULL DEFAULT '',
            suggested_prompt TEXT NOT NULL DEFAULT '',
            recommendation TEXT NOT NULL DEFAULT '',
            expected_effect TEXT NOT NULL DEFAULT '',
            confidence INTEGER NOT NULL DEFAULT 50,
            priority INTEGER NOT NULL DEFAULT 50,
            simulation TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'candidate',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(run_id) REFERENCES learning_runs(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_learning_improvements_run ON learning_improvements(run_id, priority, confidence)",
        "CREATE INDEX IF NOT EXISTS idx_learning_improvements_type ON learning_improvements(improvement_type, status, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id {id_column},
            prompt_name TEXT NOT NULL,
            version TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            target_agent TEXT NOT NULL DEFAULT '',
            prompt_template TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'draft',
            scope_type TEXT NOT NULL DEFAULT 'workspace',
            scope_id INTEGER NOT NULL DEFAULT 1,
            UNIQUE(prompt_name, version),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_prompt_versions_name_status ON prompt_versions(prompt_name, status, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_versions_scope ON prompt_versions(scope_type, scope_id, prompt_name, status)",
        f"""
        CREATE TABLE IF NOT EXISTS experiments (
            id {id_column},
            experiment_name TEXT NOT NULL,
            target_prompt TEXT NOT NULL,
            control_version TEXT NOT NULL,
            candidate_version TEXT NOT NULL,
            traffic_ratio INTEGER NOT NULL DEFAULT 50,
            status TEXT NOT NULL DEFAULT 'draft',
            start_at TEXT,
            end_at TEXT,
            winner TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            scope_type TEXT NOT NULL DEFAULT 'workspace',
            scope_id INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_experiments_prompt_status ON experiments(target_prompt, status, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_experiments_scope ON experiments(scope_type, scope_id, target_prompt, status)",
        f"""
        CREATE TABLE IF NOT EXISTS experiment_assignments (
            id {id_column},
            experiment_id INTEGER,
            project_id INTEGER,
            user_id INTEGER,
            selected_version TEXT NOT NULL,
            assignment_key TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(experiment_id) REFERENCES experiments(id),
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_experiment_assignments_experiment ON experiment_assignments(experiment_id, selected_version)",
        f"""
        CREATE TABLE IF NOT EXISTS prompt_experiment_metrics (
            id {id_column},
            experiment_id INTEGER,
            prompt_name TEXT NOT NULL,
            prompt_version TEXT NOT NULL,
            project_id INTEGER,
            outcome TEXT NOT NULL DEFAULT '',
            review_count INTEGER NOT NULL DEFAULT 0,
            quality_gate_passed INTEGER NOT NULL DEFAULT 0,
            proposal_time_seconds INTEGER NOT NULL DEFAULT 0,
            user_rating TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(experiment_id) REFERENCES experiments(id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_prompt_metrics_prompt_version ON prompt_experiment_metrics(prompt_name, prompt_version, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS feedback_entries (
            id {id_column},
            user_id INTEGER,
            user_role TEXT NOT NULL DEFAULT '',
            rating TEXT NOT NULL CHECK(rating IN ('usable', 'needs_revision', 'hard_to_use')),
            comment TEXT NOT NULL DEFAULT '',
            feature_name TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS analytics_sessions (
            id {id_column},
            session_key TEXT NOT NULL UNIQUE,
            user_id INTEGER,
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ended_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            duration_seconds INTEGER NOT NULL DEFAULT 0,
            generation_count INTEGER NOT NULL DEFAULT 0,
            download_count INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS analytics_events (
            id {id_column},
            session_key TEXT NOT NULL,
            user_id INTEGER,
            event_name TEXT NOT NULL,
            feature_name TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'success',
            duration_ms INTEGER NOT NULL DEFAULT 0,
            metadata TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_analytics_events_session ON analytics_events(session_key, event_name, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_analytics_events_feature ON analytics_events(feature_name, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS analytics_errors (
            id {id_column},
            error_key TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL DEFAULT '',
            message TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT '',
            count INTEGER NOT NULL DEFAULT 1,
            first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            resolved INTEGER NOT NULL DEFAULT 0
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS release_notes (
            id {id_column},
            version TEXT NOT NULL,
            release_date TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            improvements TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS release_records (
            id {id_column},
            version TEXT NOT NULL,
            release_date TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            summary TEXT NOT NULL DEFAULT '',
            changes TEXT NOT NULL DEFAULT '',
            impact_scope TEXT NOT NULL DEFAULT '',
            checklist TEXT NOT NULL DEFAULT '',
            known_issues TEXT NOT NULL DEFAULT '',
            rollback_note TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            released_by INTEGER,
            released_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(id),
            FOREIGN KEY(released_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_release_records_status ON release_records(status, release_date, id)",
        f"""
        CREATE TABLE IF NOT EXISTS proposal_knowledge (
            id {id_column},
            industry TEXT NOT NULL DEFAULT '',
            company_size TEXT NOT NULL DEFAULT '',
            project_summary TEXT NOT NULL DEFAULT '',
            adopted_proposal TEXT NOT NULL DEFAULT '',
            proposal_story TEXT NOT NULL DEFAULT '',
            adoption_reason TEXT NOT NULL DEFAULT '',
            lost_reason TEXT NOT NULL DEFAULT '',
            result TEXT NOT NULL DEFAULT '',
            owner_memo TEXT NOT NULL DEFAULT '',
            outcome TEXT NOT NULL DEFAULT 'unknown',
            rating INTEGER NOT NULL DEFAULT 3,
            evaluation_status TEXT NOT NULL DEFAULT 'effective',
            tags TEXT NOT NULL DEFAULT '',
            approval_status TEXT NOT NULL DEFAULT 'draft',
            quality_score INTEGER NOT NULL DEFAULT 50,
            confidential_risk TEXT NOT NULL DEFAULT 'low',
            confidential_flags TEXT NOT NULL DEFAULT '',
            source_type TEXT NOT NULL DEFAULT 'admin_created',
            source_note TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_proposal_knowledge_industry ON proposal_knowledge(industry, rating, outcome)",
        f"""
        CREATE TABLE IF NOT EXISTS proposal_templates (
            id {id_column},
            category TEXT NOT NULL DEFAULT 'other',
            title TEXT NOT NULL,
            template_summary TEXT NOT NULL DEFAULT '',
            structure TEXT NOT NULL DEFAULT '',
            recommended_for TEXT NOT NULL DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_proposal_templates_category ON proposal_templates(category, is_active)",
        f"""
        CREATE TABLE IF NOT EXISTS workspace_conversations (
            id {id_column},
            project_id TEXT NOT NULL,
            user_id INTEGER,
            client_message_id TEXT NOT NULL DEFAULT '',
            agent_name TEXT NOT NULL DEFAULT '',
            message_type TEXT NOT NULL DEFAULT 'normal',
            message_body TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_workspace_conversations_project ON workspace_conversations(project_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_workspace_conversations_client_id ON workspace_conversations(project_id, user_id, client_message_id)",
        f"""
        CREATE TABLE IF NOT EXISTS workspace_work_logs (
            id {id_column},
            project_id TEXT NOT NULL,
            user_id INTEGER,
            client_log_id TEXT NOT NULL DEFAULT '',
            agent_name TEXT NOT NULL DEFAULT '',
            action_summary TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_workspace_work_logs_project ON workspace_work_logs(project_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_workspace_work_logs_client_id ON workspace_work_logs(project_id, user_id, client_log_id)",
        f"""
        CREATE TABLE IF NOT EXISTS proposal_reviews (
            id {id_column},
            project_id TEXT NOT NULL,
            project_name TEXT NOT NULL DEFAULT '',
            creator_user_id INTEGER,
            status TEXT NOT NULL DEFAULT 'draft',
            review_comment TEXT NOT NULL DEFAULT '',
            reviewer_user_id INTEGER,
            review_requested_at TEXT,
            reviewed_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(creator_user_id) REFERENCES users(id),
            FOREIGN KEY(reviewer_user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_proposal_reviews_project ON proposal_reviews(project_id, updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_proposal_reviews_status ON proposal_reviews(status, updated_at)",
        f"""
        CREATE TABLE IF NOT EXISTS proposal_review_revisions (
            id {id_column},
            review_id INTEGER NOT NULL,
            project_id TEXT NOT NULL,
            previous_status TEXT NOT NULL DEFAULT '',
            next_status TEXT NOT NULL DEFAULT '',
            review_comment TEXT NOT NULL DEFAULT '',
            ai_improvement_policy TEXT NOT NULL DEFAULT '',
            diff_summary TEXT NOT NULL DEFAULT '',
            executed_by_user_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(review_id) REFERENCES proposal_reviews(id),
            FOREIGN KEY(executed_by_user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_proposal_review_revisions_review ON proposal_review_revisions(review_id, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS quality_gates (
            id {id_column},
            project_id TEXT NOT NULL,
            user_id INTEGER,
            checklist_items TEXT NOT NULL DEFAULT '',
            completed INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT,
            bypassed INTEGER NOT NULL DEFAULT 0,
            bypass_reason TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_quality_gates_project ON quality_gates(project_id, updated_at)",
        f"""
        CREATE TABLE IF NOT EXISTS beautiful_ai_presentations (
            id {id_column},
            project_id TEXT NOT NULL,
            user_id INTEGER,
            presentation_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            editor_url TEXT NOT NULL DEFAULT '',
            player_url TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'created',
            theme_id TEXT NOT NULL DEFAULT '',
            provider TEXT NOT NULL DEFAULT 'beautiful.ai',
            request_summary TEXT NOT NULL DEFAULT '',
            error_type TEXT NOT NULL DEFAULT '',
            http_status INTEGER NOT NULL DEFAULT 0,
            response_text TEXT NOT NULL DEFAULT '',
            request_json_safe TEXT NOT NULL DEFAULT '',
            endpoint TEXT NOT NULL DEFAULT '',
            api_mode TEXT NOT NULL DEFAULT 'prompt',
            workspace_config_id TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_beautiful_ai_presentations_project ON beautiful_ai_presentations(project_id, updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_beautiful_ai_presentations_presentation ON beautiful_ai_presentations(presentation_id)",
        f"""
        CREATE TABLE IF NOT EXISTS presentation_reviews (
            id {id_column},
            project_id TEXT NOT NULL,
            project_name TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            average_score REAL NOT NULL DEFAULT 0,
            scores_json TEXT NOT NULL DEFAULT '',
            issues_json TEXT NOT NULL DEFAULT '',
            improvements_json TEXT NOT NULL DEFAULT '',
            actions_json TEXT NOT NULL DEFAULT '',
            outline_json TEXT NOT NULL DEFAULT '',
            improvement_summary TEXT NOT NULL DEFAULT '',
            improvement_count INTEGER NOT NULL DEFAULT 0,
            unresolved_issue_count INTEGER NOT NULL DEFAULT 0,
            score_schema_version TEXT NOT NULL DEFAULT '19.1',
            approved INTEGER NOT NULL DEFAULT 0,
            beautiful_ai_presentation_id TEXT NOT NULL DEFAULT '',
            organization_id INTEGER NOT NULL DEFAULT 1,
            workspace_id INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_presentation_reviews_project ON presentation_reviews(project_id, updated_at)",
        f"""
        CREATE TABLE IF NOT EXISTS presentation_revisions (
            id {id_column},
            project_id TEXT NOT NULL,
            review_id INTEGER,
            revision_number INTEGER NOT NULL DEFAULT 1,
            revision_label TEXT NOT NULL DEFAULT '',
            slide_count INTEGER NOT NULL DEFAULT 0,
            added_slide_count INTEGER NOT NULL DEFAULT 0,
            removed_slide_count INTEGER NOT NULL DEFAULT 0,
            modified_slide_count INTEGER NOT NULL DEFAULT 0,
            improvement_summary TEXT NOT NULL DEFAULT '',
            beautiful_ai_presentation_id TEXT NOT NULL DEFAULT '',
            editor_url TEXT NOT NULL DEFAULT '',
            player_url TEXT NOT NULL DEFAULT '',
            approved INTEGER NOT NULL DEFAULT 0,
            approved_by INTEGER,
            approved_at TEXT,
            created_by INTEGER,
            status TEXT NOT NULL DEFAULT 'draft',
            selected_actions_json TEXT NOT NULL DEFAULT '',
            outline_json TEXT NOT NULL DEFAULT '',
            diff_json TEXT NOT NULL DEFAULT '',
            generation_error_type TEXT NOT NULL DEFAULT '',
            generated_at TEXT,
            organization_id INTEGER NOT NULL DEFAULT 1,
            workspace_id INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(review_id) REFERENCES presentation_reviews(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_presentation_revisions_project ON presentation_revisions(project_id, revision_number)",
        f"""
        CREATE TABLE IF NOT EXISTS presentation_revision_history (
            id {id_column},
            project_id TEXT NOT NULL,
            from_revision_id INTEGER,
            to_revision_id INTEGER NOT NULL,
            change_type TEXT NOT NULL DEFAULT '',
            change_summary TEXT NOT NULL DEFAULT '',
            change_reason TEXT NOT NULL DEFAULT '',
            before_summary TEXT NOT NULL DEFAULT '',
            after_summary TEXT NOT NULL DEFAULT '',
            field_name TEXT NOT NULL DEFAULT '',
            human_action TEXT NOT NULL DEFAULT '',
            action_id TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            organization_id INTEGER NOT NULL DEFAULT 1,
            workspace_id INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(from_revision_id) REFERENCES presentation_revisions(id),
            FOREIGN KEY(to_revision_id) REFERENCES presentation_revisions(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_presentation_revision_history_project ON presentation_revision_history(project_id, to_revision_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_presentation_revisions_scope_number_unique ON presentation_revisions(organization_id, workspace_id, project_id, revision_number)",
        f"""
        CREATE TABLE IF NOT EXISTS proposal_improvement_backlog (
            id {id_column},
            project_id TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            priority TEXT NOT NULL DEFAULT 'Medium',
            impact REAL NOT NULL DEFAULT 0,
            confidence REAL NOT NULL DEFAULT 0,
            expected_improvement REAL NOT NULL DEFAULT 0,
            effort INTEGER NOT NULL DEFAULT 3,
            importance INTEGER NOT NULL DEFAULT 3,
            adoption_rate REAL NOT NULL DEFAULT 0,
            predicted_win_rate_delta REAL NOT NULL DEFAULT 0,
            composite_score REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'suggested',
            owner INTEGER,
            source_type TEXT NOT NULL DEFAULT 'optimization_engine',
            explanation TEXT NOT NULL DEFAULT '',
            simulation_json TEXT NOT NULL DEFAULT '',
            evidence_type TEXT NOT NULL DEFAULT 'insufficient_data',
            sample_size INTEGER NOT NULL DEFAULT 0,
            is_estimate INTEGER NOT NULL DEFAULT 1,
            calculation_method TEXT NOT NULL DEFAULT 'weighted_score_v20_1',
            predicted_effect_json TEXT NOT NULL DEFAULT '',
            measured_effect_json TEXT NOT NULL DEFAULT '',
            measurement_status TEXT NOT NULL DEFAULT 'pending',
            measured_at TEXT,
            measurement_period TEXT NOT NULL DEFAULT '',
            outcome_type TEXT NOT NULL DEFAULT '',
            requires_human_review INTEGER NOT NULL DEFAULT 1,
            evidence_summary TEXT NOT NULL DEFAULT '',
            evidence_period TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            approved_by INTEGER,
            approved_at TEXT,
            organization_id INTEGER NOT NULL DEFAULT 1,
            workspace_id INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(owner) REFERENCES users(id),
            FOREIGN KEY(created_by) REFERENCES users(id),
            FOREIGN KEY(approved_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_proposal_improvement_backlog_scope ON proposal_improvement_backlog(organization_id, workspace_id, status, composite_score)",
        f"""
        CREATE TABLE IF NOT EXISTS proposal_best_practices (
            id {id_column},
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            pattern_summary TEXT NOT NULL DEFAULT '',
            source_type TEXT NOT NULL DEFAULT 'learning',
            success_metric TEXT NOT NULL DEFAULT '',
            confidence REAL NOT NULL DEFAULT 0,
            adoption_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending_review',
            normalized_title TEXT NOT NULL DEFAULT '',
            tags TEXT NOT NULL DEFAULT '',
            structure_summary TEXT NOT NULL DEFAULT '',
            cta_type TEXT NOT NULL DEFAULT '',
            slide_order_pattern TEXT NOT NULL DEFAULT '',
            evidence_count INTEGER NOT NULL DEFAULT 0,
            evidence_period TEXT NOT NULL DEFAULT '',
            confidential_risk TEXT NOT NULL DEFAULT 'low',
            quality_score INTEGER NOT NULL DEFAULT 50,
            has_prediction INTEGER NOT NULL DEFAULT 0,
            approved_by INTEGER,
            approved_at TEXT,
            approval_reason TEXT NOT NULL DEFAULT '',
            rejection_reason TEXT NOT NULL DEFAULT '',
            archived_reason TEXT NOT NULL DEFAULT '',
            merged_into_id INTEGER,
            organization_id INTEGER NOT NULL DEFAULT 1,
            workspace_id INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_proposal_best_practices_scope ON proposal_best_practices(organization_id, workspace_id, category, confidence)",
    ]
