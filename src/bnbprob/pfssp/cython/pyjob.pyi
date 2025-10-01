class PyJob:
    """Python wrapper for C++ Job class used in PFSSP
    (Permutation Flow Shop Scheduling Problem).
    """

    def __repr__(self) -> str: ...

    def __str__(self) -> str: ...

    @property
    def _signature(self) -> str:
        """String signature for the job."""
        ...

    @property
    def j(self) -> int:
        """Job index identifier."""
        ...

    @property
    def p(self) -> list[int]:
        """Processing times for each machine."""
        ...

    @property
    def r(self) -> list[int]:
        """Release times for each machine."""
        ...

    @property
    def q(self) -> list[int]:
        """Tail times for each machine."""
        ...

    @property
    def lat(self) -> list[list[int]]:
        """Lag times matrix between machines."""
        ...

    @property
    def T(self) -> int:
        """Total processing time."""
        ...

    @property
    def slope(self) -> int:
        """Slope value for the job."""
        ...

    @staticmethod
    def from_p(j: int, p: list[int]) -> 'PyJob':
        """Create PyJob from job index and processing times.

        Parameters
        ----------
        j : int
            Job index identifier

        p : list[int]
            Processing times for each machine

        Returns
        -------
        PyJob
            New PyJob instance
        """
        ...

    def get_j(self) -> int:
        """Get job index identifier.

        Returns
        -------
        int
            Job index identifier

        Raises
        ------
        ReferenceError
            If C++ Job shared pointer not initialized
        """
        ...

    def get_p(self) -> list[int]:
        """Get processing times for each machine.

        Returns
        -------
        list[int]
            Processing times for each machine

        Raises
        ------
        ReferenceError
            If C++ Job shared pointer not initialized
        """
        ...

    def get_r(self) -> list[int]:
        """Get release times for each machine.

        Returns
        -------
        list[int]
            Release times for each machine

        Raises
        ------
        ReferenceError
            If C++ Job shared pointer not initialized
        """
        ...

    def get_q(self) -> list[int]:
        """Get tail times for each machine.

        Returns
        -------
        list[int]
            Tail times for each machine

        Raises
        ------
        ReferenceError
            If C++ Job shared pointer not initialized
        """
        ...

    def get_lat(self) -> list[list[int]]:
        """Get lag times matrix between machines.

        Returns
        -------
        list[list[int]]
            Lag times matrix between machines

        Raises
        ------
        ReferenceError
            If C++ Job shared pointer not initialized
        """
        ...

    def get_slope(self) -> int:
        """Get slope value for the job.

        Returns
        -------
        int
            Slope value for the job

        Raises
        ------
        ReferenceError
            If C++ Job shared pointer not initialized
        """
        ...

    def get_T(self) -> int:
        """Get total processing time.

        Returns
        -------
        int
            Total processing time

        Raises
        ------
        ReferenceError
            If C++ Job shared pointer not initialized
        """
        ...
