"""Professional Process Management for Agent Orchestrator.

This module provides enterprise-grade process lifecycle management including:
- Process creation and monitoring
- Resource tracking (CPU, memory)
- Automatic restart with exponential backoff
- Graceful shutdown handling
- Process pool management
- Health monitoring and metrics
"""

import asyncio
import subprocess
import psutil
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum
import logfire


class ProcessState(str, Enum):
    """Process lifecycle states."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    RESTARTING = "restarting"


@dataclass
class ProcessMetrics:
    """Process resource metrics."""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    num_threads: int = 0
    open_files: int = 0
    connections: int = 0
    uptime_seconds: float = 0.0
    restart_count: int = 0


@dataclass
class ProcessConfig:
    """Configuration for process management."""
    # Restart policy
    auto_restart: bool = True
    max_restart_attempts: int = 5
    restart_delay_base: float = 1.0  # Base delay in seconds
    restart_delay_max: float = 60.0  # Max delay in seconds
    
    # Resource limits
    max_memory_mb: Optional[float] = None
    max_cpu_percent: Optional[float] = None
    
    # Timeouts
    startup_timeout: float = 30.0
    shutdown_timeout: float = 10.0
    health_check_interval: float = 30.0
    
    # Process options
    capture_output: bool = True
    working_directory: Optional[Path] = None
    environment: Optional[Dict[str, str]] = None
    
    # Callbacks (set BEFORE process starts to avoid race conditions)
    on_output: Optional[callable] = None  # Called for each stdout line
    on_error: Optional[callable] = None   # Called for each stderr line
    on_exit: Optional[callable] = None    # Called when process exits


@dataclass
class ManagedProcess:
    """Managed process instance."""
    process_id: str
    command: List[str]
    config: ProcessConfig
    
    # Process state
    state: ProcessState = ProcessState.STARTING
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    psutil_process: Optional[psutil.Process] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    
    # Metrics and monitoring
    metrics: ProcessMetrics = field(default_factory=ProcessMetrics)
    restart_attempts: int = 0
    last_restart_at: Optional[datetime] = None
    
    # Output capture
    stdout_lines: List[str] = field(default_factory=list)
    stderr_lines: List[str] = field(default_factory=list)
    max_output_lines: int = 1000
    
    # Callbacks (initialized from config to avoid race conditions)
    on_output: Optional[Callable[[str], None]] = None
    on_error: Optional[Callable[[str], None]] = None
    on_exit: Optional[Callable[[int], None]] = None
    
    def __post_init__(self):
        """Initialize callbacks from config."""
        if self.config.on_output:
            self.on_output = self.config.on_output
        if self.config.on_error:
            self.on_error = self.config.on_error
        if self.config.on_exit:
            self.on_exit = self.config.on_exit


class ProcessManager:
    """Professional process lifecycle manager.
    
    Features:
    - Automatic process monitoring and restart
    - Resource usage tracking
    - Graceful shutdown handling
    - Output capture and streaming
    - Health checking
    - Process pool management
    """
    
    def __init__(self):
        """Initialize process manager."""
        self.processes: Dict[str, ManagedProcess] = {}
        self._monitor_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._lock = asyncio.Lock()
        
    async def start(self):
        """Start the process manager."""
        logfire.info("Starting process manager")
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
    async def stop(self):
        """Stop the process manager and all processes."""
        logfire.info("Stopping process manager")
        self._shutdown_event.set()
        
        # Cancel monitoring
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop all processes
        await self.stop_all_processes()
        
    async def create_process(
        self,
        process_id: str,
        command: List[str],
        config: Optional[ProcessConfig] = None
    ) -> ManagedProcess:
        """Create and start a managed process.
        
        Args:
            process_id: Unique process identifier
            command: Command and arguments to execute
            config: Process configuration
            
        Returns:
            Managed process instance
            
        Raises:
            ValueError: If process_id already exists
            RuntimeError: If process fails to start
        """
        async with self._lock:
            if process_id in self.processes:
                raise ValueError(f"Process {process_id} already exists")
            
            config = config or ProcessConfig()
            
            managed_process = ManagedProcess(
                process_id=process_id,
                command=command,
                config=config
            )
            
            self.processes[process_id] = managed_process
            
        # Start the process
        await self._start_process(managed_process)
        
        return managed_process
    
    async def _start_process(self, managed_process: ManagedProcess):
        """Start a managed process.
        
        Args:
            managed_process: Process to start
        """
        try:
            managed_process.state = ProcessState.STARTING
            
            logfire.info(
                f"Starting process {managed_process.process_id}",
                command=" ".join(managed_process.command)
            )
            
            # Prepare process arguments
            kwargs: Dict[str, Any] = {
                "start_new_session": True,
                "text": True,
                "bufsize": 1,  # Line buffered
            }
            
            if managed_process.config.capture_output:
                kwargs["stdout"] = subprocess.PIPE
                kwargs["stderr"] = subprocess.PIPE
            
            if managed_process.config.working_directory:
                kwargs["cwd"] = str(managed_process.config.working_directory)
            
            if managed_process.config.environment:
                kwargs["env"] = managed_process.config.environment
            
            # Start process
            process = subprocess.Popen(
                managed_process.command,
                **kwargs
            )
            
            managed_process.process = process
            managed_process.pid = process.pid
            managed_process.started_at = datetime.now(timezone.utc)
            
            # Create psutil process for monitoring
            try:
                managed_process.psutil_process = psutil.Process(process.pid)
            except psutil.NoSuchProcess:
                raise RuntimeError("Process died immediately after start")
            
            # Start output readers if capturing
            if managed_process.config.capture_output:
                asyncio.create_task(
                    self._read_output(managed_process, process.stdout, is_stderr=False)
                )
                asyncio.create_task(
                    self._read_output(managed_process, process.stderr, is_stderr=True)
                )
            
            # Wait for startup (with timeout)
            startup_success = await self._wait_for_startup(
                managed_process,
                managed_process.config.startup_timeout
            )
            
            if startup_success:
                managed_process.state = ProcessState.RUNNING
                logfire.info(
                    f"Process {managed_process.process_id} started",
                    pid=process.pid
                )
            else:
                managed_process.state = ProcessState.FAILED
                raise RuntimeError("Process startup timeout")
                
        except Exception as e:
            logfire.error(
                f"Failed to start process {managed_process.process_id}",
                error=str(e)
            )
            managed_process.state = ProcessState.FAILED
            raise
    
    async def _wait_for_startup(
        self,
        managed_process: ManagedProcess,
        timeout: float
    ) -> bool:
        """Wait for process to complete startup.
        
        Args:
            managed_process: Process to monitor
            timeout: Max wait time in seconds
            
        Returns:
            True if startup successful
        """
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check if process is still alive
            if managed_process.process and managed_process.process.poll() is not None:
                return False
            
            # Simple check - if process survives 2 seconds, consider it started
            if (asyncio.get_event_loop().time() - start_time) > 2:
                return True
            
            await asyncio.sleep(0.1)
        
        return False
    
    async def _read_output(
        self,
        managed_process: ManagedProcess,
        stream,
        is_stderr: bool
    ):
        """Read and capture process output.
        
        Args:
            managed_process: Process to read from
            stream: Output stream (stdout or stderr)
            is_stderr: True if reading from stderr
        """
        try:
            while True:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, stream.readline
                )
                
                if not line:
                    break
                
                line = line.strip()
                
                # Store output (with limit)
                output_list = (
                    managed_process.stderr_lines if is_stderr
                    else managed_process.stdout_lines
                )
                
                output_list.append(line)
                if len(output_list) > managed_process.max_output_lines:
                    output_list.pop(0)
                
                # Call callbacks
                if is_stderr and managed_process.on_error:
                    managed_process.on_error(line)
                elif not is_stderr and managed_process.on_output:
                    managed_process.on_output(line)
                    
        except Exception as e:
            logfire.debug(
                f"Error reading output for {managed_process.process_id}",
                error=str(e)
            )
    
    async def stop_process(
        self,
        process_id: str,
        timeout: Optional[float] = None
    ) -> bool:
        """Stop a managed process gracefully.
        
        Args:
            process_id: Process to stop
            timeout: Shutdown timeout (uses config default if None)
            
        Returns:
            True if stopped successfully
        """
        managed_process = self.processes.get(process_id)
        if not managed_process:
            logfire.warning(f"Process {process_id} not found")
            return False
        
        if managed_process.state in [ProcessState.STOPPED, ProcessState.STOPPING]:
            return True
        
        managed_process.state = ProcessState.STOPPING
        timeout = timeout or managed_process.config.shutdown_timeout
        
        try:
            if not managed_process.psutil_process:
                return True
            
            logfire.info(f"Stopping process {process_id}", pid=managed_process.pid)
            
            # Try graceful termination
            managed_process.psutil_process.terminate()
            
            # Wait for process to exit
            try:
                managed_process.psutil_process.wait(timeout=timeout)
                success = True
            except psutil.TimeoutExpired:
                # Force kill if timeout
                logfire.warning(
                    f"Process {process_id} did not terminate gracefully, killing"
                )
                managed_process.psutil_process.kill()
                managed_process.psutil_process.wait(timeout=2)
                success = True
            
            managed_process.state = ProcessState.STOPPED
            managed_process.stopped_at = datetime.now(timezone.utc)
            
            # Call exit callback
            if managed_process.on_exit and managed_process.process:
                exit_code = managed_process.process.poll()
                if exit_code is not None:
                    managed_process.on_exit(exit_code)
            
            logfire.info(f"Process {process_id} stopped")
            return success
            
        except psutil.NoSuchProcess:
            managed_process.state = ProcessState.STOPPED
            return True
        except Exception as e:
            logfire.error(f"Failed to stop process {process_id}", error=str(e))
            managed_process.state = ProcessState.FAILED
            return False
    
    async def stop_all_processes(self):
        """Stop all managed processes."""
        logfire.info("Stopping all processes")
        
        tasks = []
        for process_id in list(self.processes.keys()):
            tasks.append(self.stop_process(process_id))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def restart_process(self, process_id: str) -> bool:
        """Restart a managed process.
        
        Args:
            process_id: Process to restart
            
        Returns:
            True if restarted successfully
        """
        managed_process = self.processes.get(process_id)
        if not managed_process:
            return False
        
        managed_process.state = ProcessState.RESTARTING
        managed_process.restart_attempts += 1
        managed_process.last_restart_at = datetime.now(timezone.utc)
        
        logfire.info(
            f"Restarting process {process_id}",
            attempt=managed_process.restart_attempts
        )
        
        # Stop current process
        await self.stop_process(process_id, timeout=5.0)
        
        # Calculate backoff delay
        delay = min(
            managed_process.config.restart_delay_base * (2 ** managed_process.restart_attempts),
            managed_process.config.restart_delay_max
        )
        
        logfire.info(f"Waiting {delay}s before restart")
        await asyncio.sleep(delay)
        
        # Start new process
        try:
            await self._start_process(managed_process)
            managed_process.metrics.restart_count += 1
            return True
        except Exception as e:
            logfire.error(f"Failed to restart process {process_id}", error=str(e))
            managed_process.state = ProcessState.FAILED
            return False
    
    async def _monitor_loop(self):
        """Background monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                await self._check_all_processes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logfire.error("Monitor loop error", error=str(e))
    
    async def _check_all_processes(self):
        """Check health and status of all processes."""
        for process_id, managed_process in list(self.processes.items()):
            try:
                await self._check_process(managed_process)
            except Exception as e:
                logfire.error(
                    f"Error checking process {process_id}",
                    error=str(e)
                )
    
    async def _check_process(self, managed_process: ManagedProcess):
        """Check individual process health and metrics.
        
        Args:
            managed_process: Process to check
        """
        if not managed_process.psutil_process:
            return
        
        try:
            # Update metrics
            if managed_process.psutil_process.is_running():
                # CPU and memory
                managed_process.metrics.cpu_percent = (
                    managed_process.psutil_process.cpu_percent(interval=0.1)
                )
                mem_info = managed_process.psutil_process.memory_info()
                managed_process.metrics.memory_mb = mem_info.rss / (1024 * 1024)
                managed_process.metrics.memory_percent = (
                    managed_process.psutil_process.memory_percent()
                )
                
                # Thread and connection counts
                managed_process.metrics.num_threads = (
                    managed_process.psutil_process.num_threads()
                )
                
                try:
                    managed_process.metrics.open_files = len(
                        managed_process.psutil_process.open_files()
                    )
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
                
                try:
                    managed_process.metrics.connections = len(
                        managed_process.psutil_process.connections()
                    )
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
                
                # Uptime
                if managed_process.started_at:
                    uptime = datetime.now(timezone.utc) - managed_process.started_at
                    managed_process.metrics.uptime_seconds = uptime.total_seconds()
                
                managed_process.last_health_check = datetime.now(timezone.utc)
                
                # Check resource limits
                await self._check_resource_limits(managed_process)
                
            else:
                # Process died
                await self._handle_process_death(managed_process)
                
        except psutil.NoSuchProcess:
            await self._handle_process_death(managed_process)
    
    async def _check_resource_limits(self, managed_process: ManagedProcess):
        """Check if process exceeds resource limits.
        
        Args:
            managed_process: Process to check
        """
        config = managed_process.config
        metrics = managed_process.metrics
        
        # Check memory limit
        if config.max_memory_mb and metrics.memory_mb > config.max_memory_mb:
            logfire.warning(
                f"Process {managed_process.process_id} exceeds memory limit",
                memory_mb=metrics.memory_mb,
                limit=config.max_memory_mb
            )
            # Could restart or kill the process here
        
        # Check CPU limit
        if config.max_cpu_percent and metrics.cpu_percent > config.max_cpu_percent:
            logfire.warning(
                f"Process {managed_process.process_id} exceeds CPU limit",
                cpu_percent=metrics.cpu_percent,
                limit=config.max_cpu_percent
            )
    
    async def _handle_process_death(self, managed_process: ManagedProcess):
        """Handle unexpected process death.
        
        Args:
            managed_process: Dead process
        """
        if managed_process.state == ProcessState.STOPPING:
            # Expected shutdown
            return
        
        logfire.warning(
            f"Process {managed_process.process_id} died unexpectedly",
            restart_attempts=managed_process.restart_attempts
        )
        
        managed_process.state = ProcessState.FAILED
        
        # Auto-restart if configured
        if (managed_process.config.auto_restart and
            managed_process.restart_attempts < managed_process.config.max_restart_attempts):
            await self.restart_process(managed_process.process_id)
        else:
            logfire.error(
                f"Process {managed_process.process_id} failed permanently",
                restart_attempts=managed_process.restart_attempts
            )
    
    def get_process(self, process_id: str) -> Optional[ManagedProcess]:
        """Get managed process by ID.
        
        Args:
            process_id: Process identifier
            
        Returns:
            Managed process or None
        """
        return self.processes.get(process_id)
    
    def get_all_processes(self) -> List[ManagedProcess]:
        """Get all managed processes.
        
        Returns:
            List of managed processes
        """
        return list(self.processes.values())
    
    def get_process_metrics(self, process_id: str) -> Optional[ProcessMetrics]:
        """Get metrics for a process.
        
        Args:
            process_id: Process identifier
            
        Returns:
            Process metrics or None
        """
        managed_process = self.processes.get(process_id)
        return managed_process.metrics if managed_process else None
    
    async def get_process_output(
        self,
        process_id: str,
        lines: int = 100,
        include_stderr: bool = True
    ) -> Dict[str, List[str]]:
        """Get recent output from a process.
        
        Args:
            process_id: Process identifier
            lines: Number of lines to return
            include_stderr: Include stderr output
            
        Returns:
            Dict with 'stdout' and optionally 'stderr' lists
        """
        managed_process = self.processes.get(process_id)
        if not managed_process:
            return {"stdout": [], "stderr": []}
        
        result = {
            "stdout": managed_process.stdout_lines[-lines:]
        }
        
        if include_stderr:
            result["stderr"] = managed_process.stderr_lines[-lines:]
        
        return result
