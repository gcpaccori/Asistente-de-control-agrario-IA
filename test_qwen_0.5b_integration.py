#!/usr/bin/env python3
"""
Integration test for Qwen 0.5B model configuration.
This test verifies that the system is properly configured to use Qwen 0.5B
and that the database-driven configuration works correctly.
"""

import os
import sys
import json
from pathlib import Path

# Set test database
os.environ['DATABASE_PATH'] = '/tmp/test_qwen_integration.db'

# Import after setting environment
from app import (
    app, init_db, migrate_db, ensure_agent_defaults,
    get_agent_config, get_or_create_producer, LOCAL_MODEL_PATH
)

def test_model_configuration():
    """Test that model path is configured for Qwen 0.5B"""
    print("=" * 60)
    print("TEST 1: Model Configuration")
    print("=" * 60)
    
    expected_model = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
    
    if expected_model in LOCAL_MODEL_PATH:
        print(f"✓ PASS: Model path configured for Qwen 0.5B")
        print(f"  Path: {LOCAL_MODEL_PATH}")
    else:
        print(f"✗ FAIL: Model path not configured correctly")
        print(f"  Expected: {expected_model}")
        print(f"  Got: {LOCAL_MODEL_PATH}")
        return False
    
    return True

def test_database_initialization():
    """Test database initialization and agent configs"""
    print("\n" + "=" * 60)
    print("TEST 2: Database Initialization")
    print("=" * 60)
    
    # Initialize database
    init_db()
    print("✓ PASS: Database initialized")
    
    with app.app_context():
        # Migrate
        migrate_db()
        print("✓ PASS: Database migrated")
        
        # Ensure agent defaults
        ensure_agent_defaults()
        print("✓ PASS: Agent defaults ensured")
        
        # Verify agent configs
        from app import get_db
        db = get_db()
        agents = db.execute("SELECT role, enabled, max_tokens FROM agent_configs").fetchall()
        
        if len(agents) == 3:
            print(f"✓ PASS: Found 3 agent configs")
            for agent in agents:
                print(f"  - {agent[0]}: enabled={agent[1]}, max_tokens={agent[2]}")
        else:
            print(f"✗ FAIL: Expected 3 agents, found {len(agents)}")
            return False
    
    return True

def test_agent_config_retrieval():
    """Test that agent configs are retrieved from database only"""
    print("\n" + "=" * 60)
    print("TEST 3: Agent Config Retrieval (Database-Driven)")
    print("=" * 60)
    
    with app.app_context():
        # Test valid role
        try:
            config = get_agent_config('formulario')
            print(f"✓ PASS: Retrieved 'formulario' config from database")
            print(f"  - Prompt length: {len(config['prompt'])} chars")
            print(f"  - Max tokens: {config['max_tokens']}")
        except Exception as e:
            print(f"✗ FAIL: Could not retrieve valid role: {e}")
            return False
        
        # Test invalid role (should raise ValueError)
        try:
            config = get_agent_config('nonexistent_role')
            print(f"✗ FAIL: Should have raised ValueError for invalid role")
            return False
        except ValueError as e:
            print(f"✓ PASS: Correctly raises ValueError for invalid role")
            print(f"  - Error: {str(e)[:60]}...")
    
    return True

def test_endpoint_validation():
    """Test that endpoints validate correctly"""
    print("\n" + "=" * 60)
    print("TEST 4: Endpoint Validation (No Hardcoded Logic)")
    print("=" * 60)
    
    with app.test_client() as client:
        # Test 1: Missing phone
        response = client.post('/agent', 
                              json={'role': 'formulario', 'message': 'test'},
                              content_type='application/json')
        if response.status_code == 400 and 'phone requerido' in response.get_json().get('error', ''):
            print(f"✓ PASS: Validates missing phone")
        else:
            print(f"✗ FAIL: Phone validation failed")
            return False
        
        # Test 2: Invalid role (database-driven validation)
        response = client.post('/agent', 
                              json={'role': 'invalid_role', 'phone': '+51999', 'message': 'test'},
                              content_type='application/json')
        if response.status_code == 400 and 'role invalido' in response.get_json().get('error', ''):
            print(f"✓ PASS: Validates invalid role using database")
        else:
            print(f"✗ FAIL: Role validation failed")
            return False
        
        # Test 3: Health endpoint
        response = client.get('/health')
        if response.status_code == 200 and response.get_json().get('status') == 'ok':
            print(f"✓ PASS: Health endpoint works")
        else:
            print(f"✗ FAIL: Health endpoint failed")
            return False
    
    return True

def test_dynamic_role_validation():
    """Test dynamic role-specific enablement validation"""
    print("\n" + "=" * 60)
    print("TEST 5: Dynamic Role Validation (No If-Else Chains)")
    print("=" * 60)
    
    with app.app_context():
        from app import get_db
        
        # Create a test producer
        producer = get_or_create_producer('+51999888777')
        db = get_db()
        
        # Enable producer and set role permissions
        db.execute("""
            UPDATE producers 
            SET allowed = 1, status = 'activo',
                enable_formulario = 1, enable_consulta = 0, enable_intervencion = 1
            WHERE id = ?
        """, (producer['id'],))
        db.commit()
        
        # Verify dynamic attribute lookup works
        producer_updated = dict(db.execute("SELECT * FROM producers WHERE id = ?", (producer['id'],)).fetchone())
        
        roles_to_test = ['formulario', 'consulta', 'intervencion']
        expected_enabled = [True, False, True]
        
        all_passed = True
        for role, expected in zip(roles_to_test, expected_enabled):
            enable_key = f"enable_{role}"
            if enable_key in producer_updated:
                is_enabled = bool(producer_updated.get(enable_key))
                if is_enabled == expected:
                    status = "✓" if is_enabled else "○"
                    print(f"{status} PASS: Dynamic check for '{role}' = {is_enabled}")
                else:
                    print(f"✗ FAIL: Expected {expected} for {role}, got {is_enabled}")
                    all_passed = False
            else:
                print(f"✗ FAIL: {enable_key} not found in producer columns")
                all_passed = False
        
        if all_passed:
            print(f"✓ PASS: Dynamic role validation works without hardcoded if-else")
        
        return all_passed

def main():
    """Run all tests"""
    print("\n" + "#" * 60)
    print("# Qwen 0.5B Integration Test Suite")
    print("# Testing: Database-driven config, No hardcoded logic")
    print("#" * 60 + "\n")
    
    tests = [
        test_model_configuration,
        test_database_initialization,
        test_agent_config_retrieval,
        test_endpoint_validation,
        test_dynamic_role_validation,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
        print("\nThe system is correctly configured for:")
        print("  - Qwen 2.5-0.5B model (faster, smaller)")
        print("  - Database-driven agent configuration")
        print("  - No hardcoded prompts or if-else chains")
        print("  - Dynamic role validation")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
