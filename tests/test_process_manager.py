"""Tests for professional process management."""

import asyncio
import pytest
from pathlib import Path

from ct_dev_agent_orchestrator_mcp.services.process_manager import (
    ProcessManager,
    ProcessConfig,
    ProcessState,
    ManagedProcess
)


@pytest.fixture
async def process_manager():
    """Create and start process manager."""
    manager = ProcessManager()
    await manager.start()
    yield manager
    await manager.stop()


@pytest.mark.asyncio
async def test_create_simple_process(process_manager):
    """Test creating a simple process."""
    # Create a simple echo process
    managed_process = await process_manager.create_process(
        process_id="test-echo",
        command=["echo", "Hello, World!"],
        config=ProcessConfig(startup_timeout=5.0)
    )
    
    assert managed_process.process_id == "test-echo"
    assert managed_process.pid is not None
    assert managed_process.state == ProcessState.RUNNING
    
    # Wait a bit for process to complete
    await asyncio.sleep(1)
    
    # Get output
    output = await process_manager.get_process_output("test-echo")
    assert "Hello, World!" in output["stdout"]


@pytest.mark.asyncio
async def test_process_restart(process_manager):
    """Test automatic process restart."""
    # Create a process that will fail
    config = ProcessConfig(
        auto_restart=True,
        max_restart_attempts=2,
        restart_delay_base=0.5,
        startup_timeout=5.0
    )
    
    managed_process = await process_manager.create_process(
        process_id="test-failing",
        command=["sh", "-c", "exit 1"],
        config=config
    )
    
    # Wait for restart attempts
    await asyncio.sleep(3)
    
    # Check that restart was attempted
    assert managed_process.metrics.restart_count > 0


@pytest.mark.asyncio
async def test_process_metrics(process_manager):
    """Test process metrics collection."""
    # Create a long-running process
    managed_process = await process_manager.create_process(
        process_id="test-metrics",
        command=["sleep", "10"],
        config=ProcessConfig(startup_timeout=5.0)
    )
    
    # Wait for metrics to be collected
    await asyncio.sleep(2)
    
    # Get metrics
    metrics = process_manager.get_process_metrics("test-metrics")
    assert metrics is not None
    assert metrics.uptime_seconds > 0
    assert metrics.memory_mb > 0


@pytest.mark.asyncio
async def test_graceful_shutdown(process_manager):
    """Test graceful process shutdown."""
    # Create a process
    managed_process = await process_manager.create_process(
        process_id="test-shutdown",
        command=["sleep", "100"],
        config=ProcessConfig(
            shutdown_timeout=2.0,
            startup_timeout=5.0
        )
    )
    
    assert managed_process.state == ProcessState.RUNNING
    
    # Stop the process
    success = await process_manager.stop_process("test-shutdown")
    
    assert success
    assert managed_process.state == ProcessState.STOPPED


@pytest.mark.asyncio
async def test_output_capture(process_manager):
    """Test output capture functionality."""
    output_lines = []
    
    def on_output(line: str):
        output_lines.append(line)
    
    # Create a process that outputs multiple lines
    managed_process = await process_manager.create_process(
        process_id="test-output",
        command=["sh", "-c", "for i in 1 2 3; do echo Line $i; sleep 0.1; done"],
        config=ProcessConfig(
            capture_output=True,
            startup_timeout=5.0
        )
    )
    
    managed_process.on_output = on_output
    
    # Wait for all output
    await asyncio.sleep(1)
    
    # Check captured output
    output = await process_manager.get_process_output("test-output")
    assert len(output["stdout"]) >= 3
    assert any("Line 1" in line for line in output["stdout"])


@pytest.mark.asyncio
async def test_resource_limits_detection(process_manager):
    """Test resource limit detection."""
    # Create a process with low memory limit
    config = ProcessConfig(
        max_memory_mb=10.0,  # Very low limit
        max_cpu_percent=10.0,  # Very low limit
        startup_timeout=5.0
    )
    
    managed_process = await process_manager.create_process(
        process_id="test-limits",
        command=["sleep", "5"],
        config=config
    )
    
    # Wait for monitoring to check limits
    await asyncio.sleep(2)
    
    # Metrics should be collected even if limits are exceeded
    metrics = process_manager.get_process_metrics("test-limits")
    assert metrics is not None


@pytest.mark.asyncio
async def test_multiple_processes(process_manager):
    """Test managing multiple processes simultaneously."""
    # Create multiple processes
    process_ids = []
    
    for i in range(3):
        process_id = f"test-multi-{i}"
        await process_manager.create_process(
            process_id=process_id,
            command=["sleep", "5"],
            config=ProcessConfig(startup_timeout=5.0)
        )
        process_ids.append(process_id)
    
    # Check all processes are running
    all_processes = process_manager.get_all_processes()
    assert len(all_processes) >= 3
    
    # Stop all processes
    for process_id in process_ids:
        await process_manager.stop_process(process_id)


@pytest.mark.asyncio
async def test_process_death_handling(process_manager):
    """Test handling of unexpected process death."""
    config = ProcessConfig(
        auto_restart=False,  # Disable restart for this test
        startup_timeout=5.0
    )
    
    # Create a process that exits quickly
    managed_process = await process_manager.create_process(
        process_id="test-death",
        command=["sh", "-c", "sleep 1; exit 1"],
        config=config
    )
    
    # Wait for process to die
    await asyncio.sleep(3)
    
    # Process should be in FAILED state
    assert managed_process.state == ProcessState.FAILED


@pytest.mark.asyncio
async def test_restart_with_backoff(process_manager):
    """Test exponential backoff in restart attempts."""
    import time
    
    config = ProcessConfig(
        auto_restart=True,
        max_restart_attempts=3,
        restart_delay_base=1.0,
        restart_delay_max=10.0,
        startup_timeout=5.0
    )
    
    start_time = time.time()
    
    # Create a process that keeps failing
    managed_process = await process_manager.create_process(
        process_id="test-backoff",
        command=["sh", "-c", "exit 1"],
        config=config
    )
    
    # Wait for all restart attempts
    await asyncio.sleep(10)
    
    # Check that multiple restarts occurred with delays
    assert managed_process.restart_attempts >= 2
    
    # Total time should reflect backoff delays
    elapsed = time.time() - start_time
    assert elapsed >= 3  # At least sum of first backoff delays


@pytest.mark.asyncio
async def test_process_state_transitions(process_manager):
    """Test process state transitions."""
    # Create a process
    managed_process = await process_manager.create_process(
        process_id="test-states",
        command=["sleep", "10"],
        config=ProcessConfig(startup_timeout=5.0)
    )
    
    # Should start as RUNNING
    assert managed_process.state == ProcessState.RUNNING
    
    # Stop it - should become STOPPING then STOPPED
    await process_manager.stop_process("test-states")
    assert managed_process.state == ProcessState.STOPPED


@pytest.mark.asyncio
async def test_get_all_processes(process_manager):
    """Test retrieving all managed processes."""
    # Create some processes
    for i in range(2):
        await process_manager.create_process(
            process_id=f"test-all-{i}",
            command=["sleep", "5"],
            config=ProcessConfig(startup_timeout=5.0)
        )
    
    # Get all processes
    all_processes = process_manager.get_all_processes()
    assert len(all_processes) >= 2
    
    # Verify they are ManagedProcess instances
    for process in all_processes:
        assert isinstance(process, ManagedProcess)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
