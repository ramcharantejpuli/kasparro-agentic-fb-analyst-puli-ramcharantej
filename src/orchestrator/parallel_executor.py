"""Parallel execution for independent agent tasks."""
import concurrent.futures
from typing import Dict, Any, List, Callable
import time


class ParallelExecutor:
    """Executes independent agent tasks in parallel."""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
    
    def execute_parallel(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute multiple independent tasks in parallel.
        
        Args:
            tasks: List of task dicts with 'name', 'func', and 'args'
        
        Returns:
            Dict mapping task names to results
        """
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(task['func'], *task.get('args', [])): task['name']
                for task in tasks
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    results[task_name] = future.result()
                except Exception as e:
                    results[task_name] = {"error": str(e)}
        
        return results
    
    def execute_with_dependencies(self, task_graph: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Execute tasks respecting dependencies.
        
        Args:
            task_graph: Dict of task_id -> {func, args, depends_on}
        
        Returns:
            Dict mapping task IDs to results
        """
        results = {}
        completed = set()
        
        def can_execute(task_id: str) -> bool:
            """Check if task dependencies are met."""
            depends_on = task_graph[task_id].get('depends_on', [])
            return all(dep in completed for dep in depends_on)
        
        def get_ready_tasks() -> List[str]:
            """Get tasks ready to execute."""
            return [
                task_id for task_id in task_graph
                if task_id not in completed and can_execute(task_id)
            ]
        
        # Execute tasks in waves
        while len(completed) < len(task_graph):
            ready_tasks = get_ready_tasks()
            
            if not ready_tasks:
                # Check for circular dependencies
                remaining = set(task_graph.keys()) - completed
                raise RuntimeError(f"Circular dependency detected: {remaining}")
            
            # Execute ready tasks in parallel
            parallel_tasks = [
                {
                    'name': task_id,
                    'func': task_graph[task_id]['func'],
                    'args': task_graph[task_id].get('args', [])
                }
                for task_id in ready_tasks
            ]
            
            batch_results = self.execute_parallel(parallel_tasks)
            results.update(batch_results)
            completed.update(ready_tasks)
        
        return results
