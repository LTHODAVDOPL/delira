import contextlib

from delira import get_backends
from .decorators import make_deprecated
import os

import zipfile


class TemporaryUnzip(object):
    """
    Context manager to temporary extract a member of a zipfile
    """
    def __init__(self, zip_file: zipfile.ZipFile, name, target_dir=None):
        """

        Parameters
        ----------
        zip_file : :class:`zipfile.ZipFile`
            the zipfile to extract the member from
        name : str
            the name of the member to extract
        target_dir : str
            the target directory to extract the member to;
            default: None -> uses cwd

        """
        self._zip_file = zip_file
        self._name = name

        if target_dir is None:
            target_dir = os.getcwd()
            remove_dir = False
        else:
            remove_dir = True

        self._target_dir = target_dir
        self._remove_dir = remove_dir

    def __enter__(self):
        """
        Extracts the member on context entrance
        """
        self._zip_file.extract(self._name, self._target_dir)

    def __exit__(self, *args, **kwargs):
        """
        Deletes extracted member on context exit

        Parameters
        ----------
        *args :
            arbitrary positional arguments (ignored here,
            just provided for API-compatibility with other context managers)
        **kwargs :
            arbitrary keyword arguments (ignored here,
            just provided for API-compatibility with other context managers)

        """
        if os.path.isfile(os.path.join(self._target_dir, self._name)):
            os.remove(os.path.join(self._target_dir, self._name))

        if self._remove_dir:
            os.rmdir(self._target_dir)


if "TORCH" in get_backends():
    import torch

    class DefaultOptimWrapperTorch(object):
        """
        Class wrapping a ``torch`` optimizer to mirror the behavior of ``apex`` 
        without depending on it

        """

        @make_deprecated("'delira.models.model_utils.scale_loss' combined with "
                         "new apex.amp API (https://github.com/NVIDIA/apex)")
        def __init__(self, optimizer: torch.optim.Optimizer, *args, **kwargs):
            """

            Parameters
            ----------
            optimizer : torch.optim.Optimizer
                the actual optimizer to wrap
            *args : 
                additional positional arguments (unused)
            **kwargs : 
                additional keyword arguments (unused)

            """

            self._optimizer = optimizer

        @contextlib.contextmanager
        def scale_loss(self, loss):
            """
            Function which scales the loss in ``apex`` and yields the unscaled loss 
            here to mirror the API

            Parameters
            ----------
            loss : torch.Tensor
                the unscaled loss

            """

            yield loss
            return

        def step(self, closure=None):
            """
            Wraps the step method of the optimizer and calls the original step 
            method

            Parameters
            ----------
            closure : callable
                A closure that reevaluates the model and returns the loss. 
                Optional for most optimizers.

            """

            return self._optimizer.step(closure=closure)

        # Forward any attribute lookups
        def __getattr__(self, attr):
            return getattr(self._optimizer, attr)

        # Forward all torch.optim.Optimizer methods
        def __getstate__(self):
            return self._optimizer.__getstate__()

        def __setstate__(self, *args, **kwargs):
            return self._optimizer.__setstate__(*args, **kwargs)

        def __repr__(self):
            return self._optimizer.__repr__()

        def state_dict(self):
            return self._optimizer.state_dict()

        def load_state_dict(self, state_dict):
            return self._optimizer.load_state_dict(state_dict)

        def zero_grad(self):
            return self._optimizer.zero_grad()

        def add_param_group(self, param_group):
            return self._optimizer.add_param_group(param_group)
