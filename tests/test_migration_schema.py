"""Migration / schema validation tests (DB required).

These assert the migrated schema matches what the ORM and application expect:
tables, indexes, seed data, constraints, and the reporting view.
"""

import sqlalchemy


def _scalar(db, sql, **params):
    return db.execute(sqlalchemy.text(sql), params).scalar()


class TestSchemaObjects:
    def test_schemas_exist(self, db_session):
        for schema in ("raw_data", "analytics"):
            exists = _scalar(
                db_session,
                "SELECT count(*) FROM information_schema.schemata WHERE schema_name=:s",
                s=schema,
            )
            assert exists == 1

    def test_core_tables_exist(self, db_session):
        expected = {
            ("raw_data", "job_postings"),
            ("analytics", "fact_job_posting"),
            ("analytics", "fact_job_posting_snapshot"),
            ("analytics", "dim_company"),
            ("analytics", "dim_location"),
            ("analytics", "dim_source"),
            ("analytics", "dim_currency"),
            ("analytics", "dim_experience_level"),
            ("analytics", "dim_employment_type"),
            ("analytics", "dim_skill"),
            ("analytics", "dim_technology"),
        }
        for schema, table in expected:
            n = _scalar(
                db_session,
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema=:s AND table_name=:t",
                s=schema,
                t=table,
            )
            assert n == 1, f"missing table {schema}.{table}"


class TestIndexes:
    def test_fact_hot_path_indexes_present(self, db_session):
        idx = _scalar(
            db_session,
            "SELECT count(*) FROM pg_indexes "
            "WHERE schemaname='analytics' AND tablename='fact_job_posting'",
        )
        # 1 PK + 9 explicit indexes in the migration
        assert idx >= 9

    def test_content_hash_indexed(self, db_session):
        names = db_session.execute(
            sqlalchemy.text(
                "SELECT indexname FROM pg_indexes "
                "WHERE schemaname='analytics' AND tablename='fact_job_posting'"
            )
        ).scalars().all()
        assert any("content_hash" in n for n in names)

    def test_raw_data_gin_index_present(self, db_session):
        defs = db_session.execute(
            sqlalchemy.text(
                "SELECT indexdef FROM pg_indexes "
                "WHERE schemaname='raw_data' AND tablename='job_postings'"
            )
        ).scalars().all()
        assert any("gin" in d.lower() for d in defs)


class TestSeedData:
    def test_currencies_seeded(self, db_session):
        assert _scalar(db_session, "SELECT count(*) FROM analytics.dim_currency") >= 4

    def test_uae_cities_seeded(self, db_session):
        assert _scalar(db_session, "SELECT count(*) FROM analytics.dim_location") >= 7

    def test_experience_levels_seeded(self, db_session):
        assert _scalar(db_session, "SELECT count(*) FROM analytics.dim_experience_level") >= 7


class TestConstraintsAndView:
    def test_duplicate_check_constraint_enforced(self, db_session):
        """is_duplicate=TRUE with NULL duplicate_of_id must be rejected."""
        # Need valid FK dims first.
        comp = _scalar(db_session, "SELECT company_id FROM analytics.dim_company LIMIT 1")
        if comp is None:
            comp = _scalar(
                db_session,
                "INSERT INTO analytics.dim_company (company_name, company_name_normalized) "
                "VALUES ('TEST_ck','test_ck') RETURNING company_id",
            )
        loc = _scalar(db_session, "SELECT location_id FROM analytics.dim_location LIMIT 1")
        src = _scalar(db_session, "SELECT source_id FROM analytics.dim_source LIMIT 1")
        if src is None:
            src = _scalar(
                db_session,
                "INSERT INTO analytics.dim_source (source_name, source_type) "
                "VALUES ('TEST_src','Mock') RETURNING source_id",
            )
        raised = False
        try:
            db_session.execute(
                sqlalchemy.text(
                    "INSERT INTO analytics.fact_job_posting "
                    "(job_title, posted_date, company_id, location_id, source_id, "
                    " content_hash, is_duplicate, duplicate_of_id) "
                    "VALUES ('X', CURRENT_DATE, :c, :l, :s, 'hash', TRUE, NULL)"
                ),
                {"c": comp, "l": loc, "s": src},
            )
            db_session.flush()
        except sqlalchemy.exc.IntegrityError:
            raised = True
        finally:
            db_session.rollback()
        assert raised, "CHECK constraint check_duplicate_reference not enforced"

    def test_active_jobs_view_exists(self, db_session):
        n = _scalar(
            db_session,
            "SELECT count(*) FROM information_schema.views "
            "WHERE table_schema='analytics' AND table_name='v_active_jobs'",
        )
        assert n == 1
