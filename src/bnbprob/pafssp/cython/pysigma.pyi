from typing import Optional

from bnbprob.pafssp.cython.pyjob import PyJob
from bnbprob.pafssp.machinegraph import MachineGraph

class PySigma:
    """
    Python wrapper for the C++ Sigma class representing a partial job sequence.

    A Sigma represents a partial permutation of jobs in a scheduling problem,
    typically used in branch-and-bound algorithms for permutation flow shop
    scheduling. It maintains the current sequence of scheduled jobs and
    provides methods to extend the sequence.
    """
    m: int
    """Number of machines in the scheduling problem"""
    jobs: list[PyJob]
    """Jobs scheduled in partial sequence"""
    C: list[int]
    """Completion times on each machine for the current sequence"""

    @staticmethod
    def empty(
        m: int, edges: Optional[list[tuple[int, int]]] = None
    ) -> "PySigma":
        """Create an empty Sigma with given number of
        machines and machine graph.

        Parameters
        ----------
        m : int
            Number of machines in the scheduling problem

        edges : Optional[list[tuple[int, int]]], optional
            Machine graph edges defining precedence relationships
            between machines.
            If None (default), creates a sequential
            machine graph where each
            machine must complete before the next.

        Returns
        -------
        PySigma
            Empty Sigma instance ready for job scheduling
        """
        ...

    @staticmethod
    def from_jobs(
        m: int,
        jobs: list[PyJob],
        edges: Optional[list[tuple[int, int]]] = None,
    ) -> "PySigma":
        """Create Sigma from list of PyJob objects.

        Parameters
        ----------
        m : int
            Number of machines in the scheduling problem

        jobs : list[PyJob]
            List of PyJob objects to be scheduled in the given order

        edges : Optional[list[tuple[int, int]]], optional
            Machine graph edges defining precedence relationships
            between machines.
            If None (default), creates a sequential
            machine graph where each
            machine must complete before the next.

        Returns
        -------
        PySigma
            Sigma instance with the given jobs scheduled in order
        """
        ...

    def push_to_bottom(self, job: PyJob) -> None:
        """Push job to the bottom (end) of the sequence.

        Parameters
        ----------
        job : PyJob
            Job to be added to the end of the current sequence

        Raises
        ------
        ReferenceError
            If the Sigma is not properly initialized
        ValueError
            If the PyJob is not properly initialized
        """
        ...

    def push_to_top(self, job: PyJob) -> None:
        """Push job to the top (beginning) of the sequence.

        Parameters
        ----------
        job : PyJob
            Job to be added to the beginning of the current sequence

        Raises
        ------
        ReferenceError
            If the Sigma is not properly initialized
        ValueError
            If the PyJob is not properly initialized
        """
        ...

    def get_m(self) -> int:
        """Get number of machines.

        Returns
        -------
        int
            Number of machines in the scheduling problem

        Raises
        ------
        ReferenceError
            If the Sigma is not properly initialized
        """
        ...

    def get_jobs(self) -> list[PyJob]:
        """Get list of jobs as PyJob objects.

        Returns
        -------
        list[PyJob]
            Current sequence of scheduled jobs

        Raises
        ------
        ReferenceError
            If the Sigma is not properly initialized
        """
        ...

    def get_C(self) -> list[int]:
        """Get completion times on each machine.

        Returns completion times for the current job sequence on each machine.
        These times represent when each machine finishes processing all jobs
        in the current sequence.

        Returns
        -------
        list[int]
            Completion times indexed by machine
            (C[i] = completion time on machine i)

        Raises
        ------
        ReferenceError
            If the Sigma is not properly initialized
        """
        ...

    def get_mach_graph(self) -> MachineGraph:
        """Get machine graph defining machine precedence relationships.

        Returns
        -------
        MachineGraph
            Machine graph object containing the precedence structure

        Raises
        ------
        ReferenceError
            If the Sigma is not properly initialized
        """
        ...

    def is_empty(self) -> bool:
        """Check if sigma has no jobs.

        Returns
        -------
        bool
            True if no jobs are currently scheduled, False otherwise

        Raises
        ------
        ReferenceError
            If the Sigma is not properly initialized
        """
        ...

    def size(self) -> int:
        """Get number of jobs in sigma.

        Returns
        -------
        int
            Number of jobs currently scheduled in the sequence

        Raises
        ------
        ReferenceError
            If the Sigma is not properly initialized
        """
        ...
