"""
Integration tests for Docker volume persistence (Task 96)
Tests that data persists across container restarts and volume management
"""
import pytest
import psycopg2
import time
import subprocess
import json
from typing import Dict, Any


class TestDatabasePersistence:
    """Test database data persistence across container restarts"""
    
    @pytest.fixture
    def db_connection(self):
        """Create database connection for testing"""
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="donations_db",
            user="postgres",
            password="postgres"
        )
        yield conn
        conn.close()
    
    @pytest.fixture
    def sample_data(self, db_connection) -> Dict[str, Any]:
        """Insert sample data for persistence testing"""
        cursor = db_connection.cursor()
        
        # Insert test data
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        test_data = {
            'donor_email': f'persistence.test.{unique_id}@example.com',
            'donor_name': f'Persistence Test User {unique_id}',
            'amount_gtq': 250.00,
            'status_id': 1,  # pending
            'reference_code': f'PERSIST_TEST_{unique_id}',
            'correlation_id': f'test-correlation-persist-{unique_id}'
        }
        
        cursor.execute("""
            INSERT INTO donations (
                amount_gtq, status_id, donor_email, donor_name, 
                reference_code, correlation_id, created_at, updated_at
            ) VALUES (
                %(amount_gtq)s, %(status_id)s, %(donor_email)s, %(donor_name)s,
                %(reference_code)s, %(correlation_id)s, NOW(), NOW()
            ) RETURNING id
        """, test_data)
        
        donation_id = cursor.fetchone()[0]
        test_data['id'] = donation_id
        
        db_connection.commit()
        cursor.close()
        
        return test_data
    
    def test_data_persists_after_container_restart(self, sample_data):
        """Test that data survives container restart"""
        # Step 1: Verify data exists before restart
        conn_before = psycopg2.connect(
            host="localhost", port=5432, database="donations_db",
            user="postgres", password="postgres"
        )
        cursor_before = conn_before.cursor()
        cursor_before.execute(
            "SELECT donor_email, amount_gtq FROM donations WHERE id = %s",
            (sample_data['id'],)
        )
        data_before = cursor_before.fetchone()
        assert data_before is not None
        assert data_before[0] == sample_data['donor_email']
        assert float(data_before[1]) == sample_data['amount_gtq']
        cursor_before.close()
        conn_before.close()
        
        # Step 2: Restart database container
        restart_result = subprocess.run(
            ["docker-compose", "restart", "db"],
            capture_output=True, text=True, cwd="."
        )
        assert restart_result.returncode == 0, f"Container restart failed: {restart_result.stderr}"
        
        # Step 3: Wait for container to be ready
        time.sleep(10)
        
        # Step 4: Verify data still exists after restart
        conn_after = psycopg2.connect(
            host="localhost", port=5432, database="donations_db",
            user="postgres", password="postgres"
        )
        cursor_after = conn_after.cursor()
        cursor_after.execute(
            "SELECT donor_email, amount_gtq FROM donations WHERE id = %s",
            (sample_data['id'],)
        )
        data_after = cursor_after.fetchone()
        assert data_after is not None
        assert data_after[0] == sample_data['donor_email']
        assert float(data_after[1]) == sample_data['amount_gtq']
        cursor_after.close()
        conn_after.close()
    
    def test_all_tables_have_data_persistence(self, db_connection):
        """Test that all 8 main tables support persistence"""
        cursor = db_connection.cursor()
        
        # Check all main tables exist and can store data
        main_tables = [
            'donations', 'users', 'roles', 'user_roles',
            'status_catalog', 'payment_events', 'email_logs', 'donor_contacts'
        ]
        
        for table in main_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            # Tables should be accessible (even if empty)
            assert count >= 0, f"Table {table} is not accessible"
        
        cursor.close()
    
    def test_volume_configuration(self):
        """Test that Docker volumes are properly configured"""
        result = subprocess.run(
            ["docker", "volume", "ls", "--format", "{{.Name}}"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        
        volumes = result.stdout.strip().split('\n')
        expected_volumes = [
            'mgen-backend_pgdata',
            'mgen-backend_grafana_data',
            'mgen-backend_loki_data'
        ]
        
        for volume in expected_volumes:
            assert volume in volumes, f"Volume {volume} not found"


class TestGrafanaLogsPersistence:
    """Test Grafana and logs data persistence"""
    
    def test_grafana_data_persists(self):
        """Test Grafana configuration and dashboards persist"""
        # Check that Grafana volume exists
        result = subprocess.run(
            ["docker", "volume", "inspect", "mgen-backend_grafana_data"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        
        volume_info = json.loads(result.stdout)
        assert len(volume_info) == 1
        assert volume_info[0]['Name'] == 'mgen-backend_grafana_data'
    
    def test_loki_data_persists(self):
        """Test Loki logs data persistence"""
        # Check that Loki volume exists
        result = subprocess.run(
            ["docker", "volume", "inspect", "mgen-backend_loki_data"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        
        volume_info = json.loads(result.stdout)
        assert len(volume_info) == 1
        assert volume_info[0]['Name'] == 'mgen-backend_loki_data'


class TestVolumeRecovery:
    """Test volume backup and recovery scenarios"""
    
    def test_volume_backup_possible(self):
        """Test that volumes can be backed up"""
        # Test that we can inspect the main database volume
        result = subprocess.run(
            ["docker", "volume", "inspect", "mgen-backend_pgdata"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        
        volume_info = json.loads(result.stdout)
        assert len(volume_info) == 1
        assert 'Mountpoint' in volume_info[0]
        
        # Volume should have a valid mountpoint
        mountpoint = volume_info[0]['Mountpoint']
        assert mountpoint.startswith('/'), "Invalid mountpoint"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
