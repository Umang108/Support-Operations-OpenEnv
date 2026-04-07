#!/usr/bin/env python
"""
Comprehensive verification script for the Support Operations OpenEnv environment.

This script tests all major components to ensure the environment is working correctly.
Run: python verify_setup.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_success(msg: str) -> None:
    print(f"{GREEN}[OK] {msg}{RESET}")


def print_error(msg: str) -> None:
    print(f"{RED}[FAIL] {msg}{RESET}")


def print_info(msg: str) -> None:
    print(f"{YELLOW}[->] {msg}{RESET}")


def test_imports() -> bool:
    """Test that all key modules can be imported."""
    print("\n" + "=" * 60)
    print("1. Testing Imports")
    print("=" * 60)

    try:
        from support_ops_env import SupportOpsEnv, SupportOpsAction, SupportOpsObservation
        print_success("Core imports successful")

        from support_ops_env.task_bank import get_task, list_task_ids
        print_success("Task bank imports successful")

        from support_ops_env.graders import grade_task
        print_success("Graders import successful")

        from support_ops_env.server.support_ops_environment import SupportOpsEnvironment
        print_success("Server environment import successful")

        return True
    except ImportError as e:
        print_error(f"Import failed: {e}")
        return False


def test_environment_creation() -> bool:
    """Test that environment can be created and reset."""
    print("\n" + "=" * 60)
    print("2. Testing Environment Creation")
    print("=" * 60)

    try:
        from support_ops_env import SupportOpsEnv

        env = SupportOpsEnv()
        print_success("Environment created")

        result = env.reset(task_id="easy_password_reset")
        obs = result.observation
        print_success("Environment reset successful")

        assert obs.task_id == "easy_password_reset", "Task ID mismatch"
        print_success(f"Task loaded: {obs.task_title}")

        assert obs.remaining_steps > 0, "No steps available"
        print_success(f"Steps available: {obs.remaining_steps}")

        return True
    except Exception as e:
        print_error(f"Environment creation failed: {e}")
        return False


def test_all_tasks() -> bool:
    """Test that all three tasks load correctly."""
    print("\n" + "=" * 60)
    print("3. Testing All Tasks")
    print("=" * 60)

    try:
        from support_ops_env import SupportOpsEnv
        from support_ops_env.task_bank import list_task_ids

        env = SupportOpsEnv()
        tasks = list_task_ids()

        print_info(f"Tasks available: {tasks}")
        assert len(tasks) == 3, f"Expected 3 tasks, got {len(tasks)}"

        for task_id in tasks:
            result = env.reset(task_id=task_id)
            obs = result.observation
            print_success(f"  - {task_id}: {obs.task_title} ({len(obs.queue_overview)} tickets)")

        return True
    except Exception as e:
        print_error(f"Task loading failed: {e}")
        return False


def test_action_execution() -> bool:
    """Test that actions can be executed and produce rewards."""
    print("\n" + "=" * 60)
    print("4. Testing Action Execution")
    print("=" * 60)

    try:
        from support_ops_env import SupportOpsEnv, SupportOpsAction

        env = SupportOpsEnv()
        env.reset(task_id="easy_password_reset")

        # Test list_tickets
        result = env.step(SupportOpsAction(action_type="list_tickets"))
        assert result.reward is not None, "No reward returned"
        print_success("list_tickets action executed")

        # Test open_ticket
        result = env.step(SupportOpsAction(action_type="open_ticket", ticket_id="T-100"))
        assert result.observation.active_ticket is not None, "Ticket not opened"
        print_success("open_ticket action executed")

        # Test classify_ticket
        result = env.step(
            SupportOpsAction(
                action_type="classify_ticket",
                ticket_id="T-100",
                category="account_access",
                priority="normal",
            )
        )
        assert result.reward > -0.05, "Unexpected negative reward for valid action"
        print_success("classify_ticket action executed with positive reward")

        return True
    except Exception as e:
        print_error(f"Action execution failed: {e}")
        return False


def test_grading() -> bool:
    """Test that tasks can be graded and produce scores."""
    print("\n" + "=" * 60)
    print("5. Testing Task Grading")
    print("=" * 60)

    try:
        from support_ops_env import SupportOpsEnv, SupportOpsAction

        env = SupportOpsEnv()
        env.reset(task_id="easy_password_reset")

        # Execute a full correct solution
        actions = [
            SupportOpsAction(action_type="open_ticket", ticket_id="T-100"),
            SupportOpsAction(
                action_type="classify_ticket",
                ticket_id="T-100",
                category="account_access",
                priority="normal",
            ),
            SupportOpsAction(action_type="assign_ticket", ticket_id="T-100", team="identity_support"),
            SupportOpsAction(
                action_type="reply_ticket",
                ticket_id="T-100",
                message="I have sent a fresh password reset link so you can log in to your account again.",
            ),
            SupportOpsAction(action_type="set_status", ticket_id="T-100", status="resolved"),
        ]

        for action in actions:
            env.step(action)

        state = env.state()
        score = state.score_breakdown.aggregate_score

        assert 0.0 < score < 1.0, f"Invalid score (must be strictly between 0 and 1): {score}"
        print_success(f"Task graded with score: {score}")

        print_success(f"Completed objectives: {len(state.score_breakdown.completed_objectives)}")
        for obj in state.score_breakdown.completed_objectives:
            print(f"    - {obj}")

        return True
    except Exception as e:
        print_error(f"Grading failed: {e}")
        return False


def test_reward_structure() -> bool:
    """Test that reward structure is consistent."""
    print("\n" + "=" * 60)
    print("6. Testing Reward Structure")
    print("=" * 60)

    try:
        from support_ops_env import SupportOpsEnv, SupportOpsAction

        env = SupportOpsEnv()
        env.reset(task_id="easy_password_reset")

        # Test that all rewards are valid floats
        action = SupportOpsAction(action_type="list_tickets")
        result = env.step(action)

        assert isinstance(result.reward, (int, float)), "Reward is not numeric"
        assert -1.0 <= result.reward <= 1.0, f"Reward out of bounds: {result.reward}"
        print_success(f"Reward structure valid (sample reward: {result.reward})")

        # Test invalid action penalty
        env.reset(task_id="easy_password_reset")
        result = env.step(SupportOpsAction(action_type="assign_ticket", ticket_id="T-100"))
        assert result.reward < -0.05, "Invalid action not penalized"
        print_success("Invalid actions are properly penalized")

        return True
    except Exception as e:
        print_error(f"Reward structure test failed: {e}")
        return False


def test_state_consistency() -> bool:
    """Test that state() returns consistent data."""
    print("\n" + "=" * 60)
    print("7. Testing State Consistency")
    print("=" * 60)

    try:
        from support_ops_env import SupportOpsEnv, SupportOpsAction

        env = SupportOpsEnv()
        env.reset(task_id="easy_password_reset")
        env.step(SupportOpsAction(action_type="list_tickets"))

        state = env.state()

        assert state.task_id == "easy_password_reset", "Task ID mismatch"
        assert state.step_count >= 1, "Step count not incremented"
        assert state.max_steps > 0, "Max steps invalid"
        assert len(state.tickets) > 0, "No tickets in state"
        assert state.score_breakdown is not None, "No score breakdown"

        print_success("State object is consistent")
        print_success(f"  - Step count: {state.step_count}/{state.max_steps}")
        print_success(f"  - Tickets: {len(state.tickets)}")
        print_success(f"  - Score: {state.score_breakdown.aggregate_score}")

        return True
    except Exception as e:
        print_error(f"State consistency test failed: {e}")
        return False


def test_file_structure() -> bool:
    """Test that all required files exist."""
    print("\n" + "=" * 60)
    print("8. Testing File Structure")
    print("=" * 60)

    required_files = [
        "support_ops_env/__init__.py",
        "support_ops_env/models.py",
        "support_ops_env/client.py",
        "support_ops_env/graders.py",
        "support_ops_env/task_bank.py",
        "support_ops_env/openenv_compat.py",
        "support_ops_env/server/__init__.py",
        "support_ops_env/server/app.py",
        "support_ops_env/server/__main__.py",
        "support_ops_env/server/support_ops_environment.py",
        "scripts/run_baseline.py",
        "tests/test_support_ops_env.py",
        "pyproject.toml",
        "openenv.yaml",
        "Dockerfile",
        "README.md",
    ]

    missing = []
    for file in required_files:
        path = Path(file)
        if path.exists():
            print_success(f"  - {file}")
        else:
            print_error(f"  - {file} (MISSING)")
            missing.append(file)

    if missing:
        print_error(f"{len(missing)} files missing")
        return False

    print_success("All required files present")
    return True


def test_docker_readiness() -> bool:
    """Test that Docker build would be successful."""
    print("\n" + "=" * 60)
    print("9. Checking Docker Readiness")
    print("=" * 60)

    dockerfile_checks = [
        ("Dockerfile exists", Path("Dockerfile").exists()),
        ("pyproject.toml exists", Path("pyproject.toml").exists()),
        ("requirements.txt exists", Path("requirements.txt").exists()),
    ]

    for check_name, result in dockerfile_checks:
        if result:
            print_success(check_name)
        else:
            print_error(check_name)

    all_passed = all(result for _, result in dockerfile_checks)

    if all_passed:
        print_success("Docker build requirements met")

    return all_passed


def main() -> None:
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("SUPPORT OPS OPENENV - VERIFICATION SCRIPT")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Environment Creation", test_environment_creation),
        ("All Tasks", test_all_tasks),
        ("Action Execution", test_action_execution),
        ("Task Grading", test_grading),
        ("Reward Structure", test_reward_structure),
        ("State Consistency", test_state_consistency),
        ("File Structure", test_file_structure),
        ("Docker Readiness", test_docker_readiness),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Test {test_name} crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = GREEN if result else RED
        print(f"{symbol}[{status}]{RESET} {test_name}")

    print("\n" + "=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print_success("Environment is fully functional!")
        print("\nNext steps:")
        print("  1. Run tests: pytest")
        print("  2. Start server: python -m support_ops_env.server")
        print("  3. Run baseline: python scripts/run_baseline.py")
        print("  4. Deploy: docker build -t support-ops-env .")
        sys.exit(0)
    else:
        print_error(f"Environment has {total - passed} failing tests")
        sys.exit(1)


if __name__ == "__main__":
    main()
